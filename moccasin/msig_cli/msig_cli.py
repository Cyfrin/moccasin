import json
import shutil
from argparse import Namespace
from typing import List, cast

from eth_typing import URI
from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from safe_eth.eth import EthereumClient
from safe_eth.safe import Safe, SafeTx

from moccasin.msig_cli.common_prompts import (
    prompt_continue_next_step,
    prompt_rpc_url,
    prompt_safe_address,
)
from moccasin.msig_cli.constants import ERROR_INVALID_RPC_URL
from moccasin.msig_cli.tx import tx_build, tx_sign
from moccasin.msig_cli.tx.sign_prompts import prompt_eip712_input_file
from moccasin.msig_cli.utils.exceptions import MsigCliError, MsigCliUserAbort
from moccasin.msig_cli.utils.helpers import (
    build_safe_tx_from_message,
    extract_safe_tx_json,
    get_safe_instance,
    get_signatures_bytes,
    validate_ethereum_client_chain_id,
)
from moccasin.msig_cli.utils.types import T_SafeTxData
from moccasin.msig_cli.validators import is_valid_rpc_url


class MsigCli:
    """MsigCli class to handle multi-signature wallet operations and session state."""

    def __init__(self):
        """Initialize the MsigCli instance."""
        self.prompt_session = PromptSession(
            auto_suggest=AutoSuggestFromHistory(),
            bottom_toolbar=self._bottom_toolbar_cli,
            rprompt=self._right_toolbar_cli,
            validate_while_typing=False,
        )
        self.ethereum_client = None
        self.safe_instance: Safe = None
        self.safe_tx: SafeTx = None

    def run(self, args: Namespace = None):
        """
        Run the msig CLI with parsed args and subcommands.
        :param msig_command: Top-level msig command (e.g., 'tx', 'msg').
        :param args: argparse Namespace with all parsed arguments.
        """
        try:
            # Check if rpc_url is provided in args or prompt for it
            rpc_url = cast(str, getattr(args, "url", None))
            if rpc_url:
                if not is_valid_rpc_url(rpc_url):
                    raise MsigCliError(ERROR_INVALID_RPC_URL)
            else:
                # Prompt for RPC URL if not provided
                rpc_url = cast(str, prompt_rpc_url(self.prompt_session))
                if not is_valid_rpc_url(rpc_url):
                    raise MsigCliError(ERROR_INVALID_RPC_URL)

            # Initialize Ethereum client with the provided or prompted RPC URL
            try:
                self.ethereum_client = EthereumClient(URI(rpc_url))
            except Exception as e:
                raise MsigCliError(f"Failed to initialize Ethereum client: {e}")
            print_formatted_text(
                HTML(
                    f"<b><green>Using ChainId: {self.ethereum_client.get_chain_id()}</green></b>"
                )
            )

            # Start the msig CLI commands based on the provided args
            if str(args.msig_command).startswith("tx_"):
                tx_command = getattr(args, "msig_command", None)
                order: List[str] = ["tx_build", "tx_sign", "tx_broadcast"]
                start_idx = order.index(tx_command) if tx_command in order else 0
                for idx in range(start_idx, len(order)):
                    cmd = order[idx]
                    if cmd == "tx_build":
                        self.msig_command = "tx_build"
                        self._tx_build_command(args)
                    elif cmd == "tx_sign":
                        self.msig_command = "tx_sign"
                        self._tx_sign_command(args)
                    elif cmd == "tx_broadcast":
                        self._tx_broadcast_command(args)

                    # Reset command in rithe toolbar after each command
                    self.msig_command = None

                    # Only prompt for next step if:
                    # 1. Not the last command in the order
                    if idx < len(order) - 1:
                        # 2. Sign onlt if we have a safe_tx after building
                        if not self.safe_tx and cmd == "tx_sign":
                            print_formatted_text(
                                HTML(
                                    "<b><red>SafeTx not created. Aborting following signing.</red></b>"
                                )
                            )
                            break

                        # 3. safe_tx has been signed with required signers
                        if (
                            cmd == "tx_sign"
                            and len(self.safe_tx.signers)
                            < self.safe_instance.retrieve_threshold()
                        ):
                            print_formatted_text(
                                HTML(
                                    "<b><red>SafeTx not signed by enough signers. Aborting following broadcasting.</red></b>"
                                )
                            )
                            break

                        # Prompt for next step
                        next_step = prompt_continue_next_step(
                            self.prompt_session, next_cmd=order[idx + 1]
                        )
                        if not next_step:
                            break
            else:
                print_formatted_text(
                    HTML(f"<b><red>Unknown command: {args.msig_command}</red></b>")
                )
                return 1

        # Handle user aborts and other exceptions
        except (EOFError, KeyboardInterrupt, MsigCliUserAbort) as e:
            raise MsigCliUserAbort(f"MsigCliAborted by user: {e}") from e
        except MsigCliError as e:
            raise MsigCliError(f"MsigCli error: {e}") from e
        except Exception as e:
            raise Exception(f"MsigCli unexpected error: {e}") from e

    def _bottom_toolbar_cli(self):
        """Return the bottom toolbar text for the prompt session."""
        chain_id = "None"
        safe_addr = "None"
        tx_signed_counter = "None"

        if self.ethereum_client:
            chain_id = self.ethereum_client.get_chain_id()
        if self.safe_instance:
            safe_addr = self.safe_instance.address
        if self.safe_tx and self.safe_instance:
            try:
                threshold = self.safe_instance.retrieve_threshold()
            except Exception:
                threshold = "?"
            try:
                signers_count = len(getattr(self.safe_tx, "signers", []))
            except Exception:
                signers_count = "?"
            tx_signed_counter = f"{signers_count}/{threshold}"

        return HTML(
            f"<cyan>ChainId: {chain_id} | Safe: {safe_addr} | Signed: {tx_signed_counter}</cyan>"
        )

    def _right_toolbar_cli(self):
        """Return the right toolbar text for the prompt session, showing the current tx command."""
        if self.msig_command:
            return HTML(
                f"<b><orange bg='ansiblack'>&lt;{self.msig_command}&gt;</orange></b>"
            )
        return HTML("<b><orange bg='ansiblack'>&lt;msig&gt;</orange></b>")

    def _tx_build_command(self, args: Namespace = None):
        """Handle the transaction building command.

        This method initializes the Safe instance and SafeTx based on the provided or prompted input,
        validates the chainId, and then runs the transaction builder.

        :param args: Optional argparse Namespace with command arguments.
        """
        print_formatted_text(
            HTML("\n\n<b><cyan>Running tx_builder command...</cyan></b>\n")
        )
        # Get args from Namespace if provided
        safe_address = getattr(args, "safe_address", None)
        to = getattr(args, "to", None)
        value = getattr(args, "value", None)
        operation = getattr(args, "operation", None)
        safe_nonce = getattr(args, "safe_nonce", None)
        data = getattr(args, "data", None)
        gas_token = getattr(args, "gas_token", None)
        json_out = getattr(args, "json_output", None)

        # Initialize Safe instance from args if provided
        if not safe_address:
            print_formatted_text(
                HTML(
                    "<b><yellow>Warning: Missing safe address from input.</yellow></b>"
                )
            )
            safe_address = prompt_safe_address(self.prompt_session)

        # Init Safe instance
        try:
            self.safe_instance = get_safe_instance(
                ethereum_client=self.ethereum_client, safe_address=safe_address
            )
        except MsigCliError as e:
            raise MsigCliError(f"Failed to initialize Safe instance: {e}") from e

        print_formatted_text(
            HTML(
                f"<b><green>Using Safe address: {self.safe_instance.address}</green></b>"
            )
        )

        # Run the transaction builder with the provided args
        try:
            self.safe_tx = tx_build.run(
                prompt_session=self.prompt_session,
                safe_instance=self.safe_instance,
                to=to,
                value=value,
                operation=operation,
                safe_nonce=safe_nonce,
                data=data,
                gas_token=gas_token,
                json_output=json_out,
            )

        # Handle specific exceptions from tx_build
        except MsigCliError as e:
            raise MsigCliError(f"Error in tx_build command: {e}") from e
        except MsigCliUserAbort as e:
            raise MsigCliUserAbort(f"User aborted tx_build command: {e}") from e
        # Catch any other exceptions and raise a generic MsigCliError
        except Exception as e:
            raise Exception(f"Unexpected error in tx_build command: {e}") from e

    def _tx_sign_command(self, args: Namespace = None):
        """Handle the transaction signing command.

        This method initializes the Safe instance and SafeTx based on the provided or prompted input file,
        validates the chainId, and then runs the signing process.

        It will go directly to signing if the SafeTx is already available,
        or prompt for the EIP-712 JSON input file if not.

        :param args: Optional argparse Namespace with command arguments.
        """
        print_formatted_text(HTML("\n\n<b><cyan>Running tx_sign command...</cyan></b>"))
        # Get args from Namespace if provided
        input_file_safe_tx = getattr(args, "input_json", None)
        output_file_safe_tx = getattr(args, "output_json", None)
        signer = getattr(args, "signer", None)

        # No prior data means we need to get the Safe from the input file
        if not self.safe_instance and not self.safe_tx:
            # Check if eip712_input_file is provided, else prompt to get it
            if not input_file_safe_tx:
                print_formatted_text(
                    HTML(
                        "<b><yellow>Warning: No input file provided. Prompting for custom or original EIP-712 JSON file.</yellow></b>"
                    )
                )
                print_formatted_text(
                    HTML(
                        "<b><magenta>Note: Advised to run tx_build before tx_sign if no input file available.</magenta></b>"
                    )
                )
                eip712_prompted_file = prompt_eip712_input_file(self.prompt_session)
                if not eip712_prompted_file.exists():
                    raise MsigCliError(
                        f"JSON file SafeTx not found: {eip712_prompted_file}."
                    )
                input_file_safe_tx = eip712_prompted_file

            # Load the JSON file
            try:
                with open(input_file_safe_tx, "r") as f:
                    input_file_raw = f.read()
                    safe_tx_json: T_SafeTxData = json.loads(input_file_raw)
            except FileNotFoundError:
                raise MsigCliError(
                    f"JSON file SafeTx not found while opening: {input_file_safe_tx}"
                )
            except json.JSONDecodeError as e:
                raise MsigCliError(
                    f"Invalid JSON format in file: {input_file_safe_tx} - {e}"
                ) from e

            # Extract SafeTx data from input file
            domain_json, message_json, signatures_json = extract_safe_tx_json(
                safe_tx_json
            )

            # Validate the domain chainId from JSON and our Ethereum client
            try:
                validate_ethereum_client_chain_id(
                    ethereum_client=self.ethereum_client, domain_json=domain_json
                )
            except MsigCliError as e:
                raise MsigCliError(
                    f"Failed to validate Ethereum client chainId: {e}"
                ) from e

            # Initialize Safe instance with the address from domain_json
            safe_address = domain_json.get("verifyingContract")
            if not safe_address:
                raise MsigCliError(
                    "Domain JSON must contain 'verifyingContract' field for Safe address."
                )
            self.safe_instance = get_safe_instance(
                ethereum_client=self.ethereum_client, safe_address=safe_address
            )
            print_formatted_text(
                HTML(
                    f"<b><green>Using Safe address: {self.safe_instance.address}</green></b>"
                )
            )

            # Initialize SafeTx with the message and signatures
            self.safe_tx = build_safe_tx_from_message(
                safe_instance=self.safe_instance,
                message_json=message_json,
                signatures_json=get_signatures_bytes(signatures_json),
            )

        # Sign the SafeTx with the provided signer
        try:
            self.safe_tx = tx_sign.run(
                prompt_session=self.prompt_session,
                safe_instance=self.safe_instance,
                safe_tx=self.safe_tx,
                output_file_safe_tx=output_file_safe_tx,
                signer=signer,
            )

        # Handle specific exceptions from tx_sign
        except MsigCliUserAbort as e:
            raise MsigCliUserAbort(f"User aborted tx_sign command: {e}") from e
        except MsigCliError as e:
            raise MsigCliError(f"MsigCli error in tx_sign command: {e}") from e
        # Catch any other exceptions and raise
        except Exception as e:
            raise Exception(f"Unexpected error in tx_sign command: {e}") from e

    def _tx_broadcast_command(self, args: Namespace = None):
        """Run the transaction broadcast command.

        :param args: Optional argparse Namespace with command arguments.
        """
        print_formatted_text(
            HTML("<b><red>tx_broadcast command not implemented yet!</red></b>")
        )
