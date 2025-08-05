from argparse import Namespace
from email import message
import json
from pathlib import Path
from typing import List

from eth_typing import URI
from eth_utils import to_checksum_address
from hexbytes import HexBytes
from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.shortcuts import clear as prompt_clear
from safe_eth.eth import EthereumClient
from safe_eth.safe import Safe, SafeTx

from moccasin.logging import logger
from moccasin.moccasin_account import MoccasinAccount
from moccasin.msig_cli.arg_parser import create_msig_parser
from moccasin.msig_cli.common_prompts import (
    prompt_continue_next_step,
    prompt_rpc_url,
    prompt_safe_address,
)
from moccasin.msig_cli.constants import ERROR_INVALID_ADDRESS, ERROR_INVALID_RPC_URL
from moccasin.msig_cli.tx import tx_build
from moccasin.msig_cli.tx.helpers import get_signatures
from moccasin.msig_cli.utils import GoBackToPrompt, T_SafeTxData
from moccasin.msig_cli.validators import (
    is_valid_address,
    is_valid_private_key,
    is_valid_rpc_url,
    validator_not_empty,
    validator_json_file,
    validator_private_key,
)


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

            elif str(args.msig_command).startswith("msg_"):
                msg_command = getattr(args, "msg_command", None)
                order = ["sign"]
                start_idx = order.index(msg_command) if msg_command in order else 0
                for idx in range(start_idx, len(order)):
                    cmd = order[idx]
                    prompt_clear()
                    if cmd == "sign":
                        self._tx_sign_command(args)

    def _tx_build_command(self, args: Namespace = None):
        """Run the transaction builder command. Accepts optional argparse args.

        :param args: Optional argparse Namespace with command arguments.
        :raises GoBackToPrompt: If the user chooses to go back to the main prompt instead of continuing.
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
        except GoBackToPrompt:
            raise

    def _tx_sign_command(self, args: Namespace = None):
        """Run the transaction signer command.

        # @TODO: refactor in own file later and need tests

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

        # If signer is not provided, prompt for it
        account: MoccasinAccount = None
        if not signer:
            is_mox_account = self.prompt_session.prompt(
                HTML(
                    "<b><orange>#tx_sign > </orange>Do you want to sign with a MoccasinAccount? (yes/no): </b>"
                ),
                placeholder=HTML("<b><grey>yes/no</grey></b>"),
                validator=validator_not_empty,
            )
            if is_mox_account.lower() in ("yes", "y"):
                # Prompt for account name
                account_name = self.prompt_session.prompt(
                    HTML(
                        "<b><orange>#tx_sign > </orange>What is the name of the MoccasinAccount? </b>"
                    ),
                    placeholder=HTML("<b><grey>account_name</grey></b>"),
                    validator=validator_not_empty,
                )
                # Prompt for password
                password = self.prompt_session.prompt(
                    HTML(
                        "<b><orange>#tx_sign > </orange>What is the password for the MoccasinAccount? </b>"
                    ),
                    placeholder=HTML("<b><grey>*******</grey></b>"),
                    is_password=True,
                    validator=validator_not_empty,
                )
                # Initialize MoccasinAccount
                try:
                    account = MoccasinAccount(
                        keystore_path_or_account_name=account_name, password=password
                    )
                except Exception as e:
                    print_formatted_text(
                        HTML(
                            f"<b><red>Error initializing MoccasinAccount: {e}</red></b>"
                        )
                    )
                    return
            else:
                # Prompt for private key
                print_formatted_text(
                    HTML(
                        "\n<b><red>Signing with private key is discouraged. Please use MoccasinAccount instead.</red></b>\n"
                    )
                )
                private_key = self.prompt_session.prompt(
                    HTML(
                        "<b><orange>#tx_sign > </orange>What is the private key of the signer? </b>"
                    ),
                    placeholder=HTML("<b><grey>0x...</grey></b>"),
                    is_password=True,
                    validator=validator_private_key,
                )
                # Initialize MoccasinAccount with private key
                try:
                    account = MoccasinAccount(private_key=private_key)
                except Exception as e:
                    print_formatted_text(
                        HTML(
                            f"<b><red>Error initializing MoccasinAccount: {e}</red></b>"
                        )
                    )
                    return
        else:
            # Check if signer is a string name or a private key
            if is_valid_private_key(signer):
                # Initialize MoccasinAccount with private key
                try:
                    account = MoccasinAccount(private_key=HexBytes(signer))
                except Exception as e:
                    print_formatted_text(
                        HTML(
                            f"<b><red>Error initializing MoccasinAccount: {e}</red></b>"
                        )
                    )
                    return
            else:
                # Assume signer is an account name and prompt for password
                try:
                    password = (
                        self.prompt_session.prompt(
                            HTML(
                                "<b><orange>#tx_sign > </orange>What is the password for the MoccasinAccount? </b>"
                            ),
                            placeholder=HTML("<b><grey>*******</grey></b>"),
                            is_password=True,
                            validator=validator_not_empty,
                        ),
                    )
                    account = MoccasinAccount(
                        keystore_path_or_account_name=signer, password=password
                    )
                except Exception as e:
                    print_formatted_text(
                        HTML(
                            f"<b><red>Error initializing MoccasinAccount: {e}</red></b>"
                        )
                    )
                    return

        # Check if account is initialized
        if account:
            # Check if the account is the right one
            is_right_account = self.prompt_session.prompt(
                HTML(
                    f"<b><orange>#tx_sign > </orange>Is this the right account? {account.address} (yes/no): </b>"
                ),
                placeholder=HTML("<b><grey>yes/no</grey></b>"),
                validator=validator_not_empty,
                is_password=False,  # @dev reset field value in session
            )
            if is_right_account.lower() not in ("yes", "y"):
                print_formatted_text(
                    HTML("<b><red>Aborting signing. Wrong account.</red></b>")
                )
                return
        else:
            # If account is not initialized, print error and return
            print_formatted_text(
                HTML(
                    "<b><red>Signer account not initialized. Aborting signing.</red></b>"
                )
            )
            return

        # Display the initialized account
        print_formatted_text(
            HTML(
                f"\n<b><green>Signer account initialized successfully: {account.address}</green></b>\n"
            )
        )

        # Check if safe_tx is initialized
        if not self.safe_tx:
            # Check if eip712_input_file is provided, else prompt to get it
            if not input_file_safe_tx:
                eip712_prompted_file = Path(
                    self.prompt_session.prompt(
                        HTML(
                            "<b><orange>#tx_sign > </orange>Could not find SafeTx. Please provide EIP-712 input file: </b>"
                        ),
                        validator=validator_json_file,
                        placeholder=HTML(
                            "<b><grey>./path/to/eip712_input.json</grey></b>"
                        ),
                    )
                )
                if not eip712_prompted_file.exists():
                    print_formatted_text(
                        HTML(f"<b><red>File not found: {input_file_safe_tx}</red></b>")
                    )
                    return
                input_file_safe_tx = eip712_prompted_file

            # Load the JSON file
            try:
                with open(input_file_safe_tx, "r") as f:
                    input_file_raw = f.read()
                    safe_tx_json: T_SafeTxData = json.loads(input_file_raw)
            except FileNotFoundError:
                print_formatted_text(
                    HTML(f"<b><red>File not found: {input_file_safe_tx}</red></b>")
                )
                return
            except json.JSONDecodeError:
                print_formatted_text(
                    HTML(
                        f"<b><red>Invalid JSON format in file: {input_file_safe_tx}</red></b>"
                    )
                )
                return

            # Get the required fields from the JSON
            safe_tx_eip712 = safe_tx_json.get("safeTx", None)
            signatures_json = safe_tx_json.get("signatures", None)

            if not safe_tx_eip712:
                print_formatted_text(
                    HTML(
                        f"<b><red>Missing 'safeTx' field in JSON file: {input_file_safe_tx}</red></b>"
                    )
                )
                return

            # Get the sigmature from:
            # 1. CLI input
            # 2. JSON file
            # 3. Default to empty bytes
            signatures = get_signatures(
                cli_signatures=signatures, json_signatures=signatures_json
            )

            # Create SafeTx
            # @FIXME: Handle error Error creating SafeTx from JSON: 'dict' object has no attribute 'to'
            message_json = safe_tx_eip712.get("message", None)
            if message_json:
                try:
                    # Convert the message to SafeTx
                    self.safe_tx = self.safe_instance.build_multisig_tx(
                        to=to_checksum_address(message_json.to),
                        value=message_json.value,
                        data=HexBytes(message_json.data).removeprefix("0x"),
                        operation=message_json.operation,
                        safe_tx_gas=message_json.safeTxGas,
                        base_gas=message_json.baseGas,
                        data_gas=message_json.dataGas,
                        gas_price=message_json.gasPrice,
                        gas_token=to_checksum_address(message_json.gasToken),
                        refund_receiver=to_checksum_address(
                            message_json.refundReceiver
                        ),
                        signatures=b"",  # @TODO: Handle signatures if needed
                        nonce=message_json.nonce,
                    )
                except Exception as e:
                    print_formatted_text(
                        HTML(f"<b><red>Error creating SafeTx from JSON: {e}</red></b>")
                    )
                    return
            else:
                print_formatted_text(
                    HTML(
                        f"<b><red>Missing 'message' field in 'safeTx' JSON: {input_file_safe_tx}</red></b>"
                    )
                )
                return

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
            logger.error(f"Failed to initialize Safe instance: {e}")
            raise e

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
                except Exception:
                    print_formatted_text(
                        HTML(
                            "\n<b><red>Failed to initialize Safe instance from arguments.</red></b>"
                        )
                    )
                    return

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
                        print_formatted_text(
                            HTML("\n<b><red>Aborted Safe initialization.</red></b>")
                        )
                        return
