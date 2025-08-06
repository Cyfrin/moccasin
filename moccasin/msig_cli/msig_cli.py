from argparse import Namespace
from typing import List

from eth_typing import URI
from eth_utils import to_checksum_address
from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.shortcuts import clear as prompt_clear
from safe_eth.eth import EthereumClient
from safe_eth.safe import Safe, SafeTx

from moccasin.msig_cli.arg_parser import create_msig_parser
from moccasin.msig_cli.common_prompts import (
    prompt_continue_next_step,
    prompt_rpc_url,
    prompt_safe_address,
)
from moccasin.msig_cli.constants import ERROR_INVALID_ADDRESS, ERROR_INVALID_RPC_URL
from moccasin.msig_cli.tx import tx_build, tx_sign
from moccasin.msig_cli.utils import MsigCliError, MsigCliUserAbort
from moccasin.msig_cli.validators import is_valid_address, is_valid_rpc_url


class MsigCli:
    """MsigCli class to handle multi-signature wallet operations and session state."""

    def __init__(self):
        """Initialize the MsigCli instance."""
        self.parser = create_msig_parser()

        self.prompt_session = PromptSession(
            auto_suggest=AutoSuggestFromHistory(),
            bottom_toolbar="Tips: Use Ctrl-C to exit.",
            validate_while_typing=False,
        )
        self.safe_instance: Safe = None
        self.safe_tx: SafeTx = None

    def run(self, args: Namespace = None):
        """
        Run the msig CLI with parsed args and subcommands.
        :param msig_command: Top-level msig command (e.g., 'tx', 'msg').
        :param args: argparse Namespace with all parsed arguments.
        """
        try:
            # Parse the command line arguments
            args = self.parser.parse_args(args)

            # If no subcommand, show msig help
            if args.msig_command is None:
                self.parser.print_help()
                return 0

            # Prepare the CLI context
            self._prepare_cli_context(args)

            # Interactive ordered workflow restoration
            if self.safe_instance:
                if str(args.msig_command).startswith("tx_"):
                    tx_command = getattr(args, "msig_command", None)
                    order: List[str] = ["tx_build", "tx_sign", "tx_broadcast"]
                    start_idx = order.index(tx_command) if tx_command in order else 0
                    for idx in range(start_idx, len(order)):
                        cmd = order[idx]
                        prompt_clear()
                        if cmd == "tx_build":
                            self._tx_build_command(args)
                        elif cmd == "tx_sign":
                            self._tx_sign_command(args)
                        elif cmd == "tx_broadcast":
                            self._tx_broadcast_command(args)

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
            else:
                print_formatted_text(
                    HTML(
                        "<b><red>Safe instance not initialized. Cannot run commands.</red></b>"
                    )
                )
                return 1

        # Handle user aborts and other exceptions
        except (EOFError, KeyboardInterrupt, MsigCliUserAbort) as e:
            raise MsigCliUserAbort(f"MsigCliAborted by user: {e}") from e
        except MsigCliError as e:
            raise MsigCliError(f"MsigCli error: {e}") from e
        except Exception as e:
            raise Exception(f"MsigCli unexpected error: {e}") from e

    def _tx_build_command(self, args: Namespace = None):
        """Run the transaction builder command. Accepts optional argparse args.

        :param args: Optional argparse Namespace with command arguments.
        """
        print_formatted_text(
            HTML("\n<b><magenta>Running tx_builder command...</magenta></b>")
        )
        # Get args from Namespace if provided
        to = getattr(args, "to", None)
        value = getattr(args, "value", None)
        operation = getattr(args, "operation", None)
        safe_nonce = getattr(args, "safe_nonce", None)
        data = getattr(args, "data", None)
        gas_token = getattr(args, "gas_token", None)
        json_out = getattr(args, "json_output", None)

        # Run the transaction builder with the provided args
        try:
            self.safe_tx = tx_build.run(
                safe_instance=self.safe_instance,
                prompt_session=self.prompt_session,
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
        """Run the transaction signer command.

        :param args: Optional argparse Namespace with command arguments.
        """
        print_formatted_text(
            HTML("\n<b><magenta>Running tx_sign command...</magenta></b>")
        )
        # Get args from Namespace if provided
        input_file_safe_tx = getattr(args, "input_json", None)
        output_file_safe_tx = getattr(args, "output_json", None)
        signer = getattr(args, "signer", None)
        signatures = getattr(args, "signatures", None)

        try:
            self.safe_tx = tx_sign.run(
                safe_instance=self.safe_instance,
                prompt_session=self.prompt_session,
                safe_tx=self.safe_tx,
                input_file_safe_tx=input_file_safe_tx,
                output_file_safe_tx=output_file_safe_tx,
                signer=signer,
                signatures=signatures,
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

    def _initialize_safe_instance(self, rpc_url: str, safe_address: str) -> Safe:
        """Initialize the Safe instance with the provided RPC URL and Safe address.

        :param rpc_url: The RPC URL to connect to the Ethereum network.
        :param safe_address: The address of the Safe contract.
        :return: An instance of the Safe class.
        :raises ValueError: If the address or RPC URL is invalid.
        """
        assert is_valid_address(safe_address), ERROR_INVALID_ADDRESS
        assert is_valid_rpc_url(rpc_url), ERROR_INVALID_RPC_URL
        try:
            ethereum_client = EthereumClient(URI(rpc_url))
            safe_address = to_checksum_address(safe_address)
            self.safe_instance = Safe(
                address=safe_address, ethereum_client=ethereum_client
            )  # type: ignore[abstract]
            print_formatted_text(
                HTML(
                    "\n<b><green>Safe instance initialized successfully!</green></b>\n"
                )
            )
            return self.safe_instance
        except Exception as e:
            raise MsigCliError(f"Failed to initialize Safe instance: {e}") from e

    def _prepare_cli_context(self, args: Namespace = None):
        """Prepare the CLI context by initializing the Safe instance and displaying the header.

        :param args: Optional argparse Namespace with command arguments.
        """

        # Default display msig CLI header
        prompt_clear()
        print_formatted_text(HTML("\n<b><cyan>===== MSIG CLI =====</cyan></b>\n"))
        print_formatted_text(
            HTML(
                f"<b><magenta>Current Safe Address:</magenta></b> {self.safe_instance.address if self.safe_instance else 'Not initialized'}"
            )
        )
        print_formatted_text(
            HTML(
                f"<b><magenta>Chain Id:</magenta></b> {self.safe_instance.chain_id if self.safe_instance else 'Not initialized'}"
            )
        )
        print_formatted_text(
            HTML(
                f"<b><magenta>SafeTx:</magenta></b> {str(self.safe_tx) if self.safe_tx else 'Not created'}\n"
            )
        )

        # If Safe instance is not initialized, try to use args, else prompt for RPC URL and Safe address
        if not self.safe_instance:
            # Initialize Safe instance from args if provided
            rpc_url = getattr(args, "rpc_url", None) if args is not None else None
            safe_address = (
                getattr(args, "safe_address", None) if args is not None else None
            )

            if rpc_url and safe_address:
                try:
                    self._initialize_safe_instance(rpc_url, safe_address)
                except MsigCliError as e:
                    raise MsigCliError(f"Error initializing Safe instance: {e}") from e

            # If not provided, prompt for RPC URL and Safe address
            else:
                print_formatted_text(
                    HTML(
                        "<b><yellow>Safe instance not initialized. Please provide RPC URL and Safe address.</yellow></b>"
                    )
                )
                while not self.safe_instance:
                    try:
                        rpc_url = prompt_rpc_url(self.prompt_session)
                        safe_address = prompt_safe_address(self.prompt_session)
                        self._initialize_safe_instance(rpc_url, safe_address)
                    except (EOFError, KeyboardInterrupt):
                        raise MsigCliUserAbort("Aborted Safe initialization by user.")
                    except MsigCliError as e:
                        print_formatted_text(HTML(f"<b><red>Error: {e}</red></b>"))
                        continue
