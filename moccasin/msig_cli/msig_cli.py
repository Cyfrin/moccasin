from eth_typing import ChecksumAddress
from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.shortcuts import clear as prompt_clear

from moccasin.logging import logger
from moccasin.msig_cli import tx_builder
from moccasin.msig_cli.constants import ERROR_INVALID_ADDRESS, ERROR_INVALID_RPC_URL
from moccasin.msig_cli.validators import is_valid_address, is_valid_rpc_url
from moccasin.msig_cli.utils import GoBackToPrompt

from safe_eth.eth import EthereumClient
from safe_eth.safe import Safe, SafeTx


class MsigCli:
    """MsigCli class to handle multi-signature wallet operations and session state."""

    def __init__(self):
        self.prompt_session = PromptSession(
            auto_suggest=AutoSuggestFromHistory(),
            bottom_toolbar="Tips: Use Ctrl-C to exit.",
            validate_while_typing=False,
        )
        self.safe_instance: Safe = None
        self.safe_tx: SafeTx = None
        # Register commands as methods or external functions, passing self and session
        self.commands = {
            "tx_builder": self._tx_builder_command,
            "tx_signer": self._tx_signer_command,
            "tx_broadcast": self._tx_broadcast_command,
        }

    def run(self, cmd: str = None, args=None):
        """Main CLI loop. If cmd is given, run it once as a shortcut, then enter the prompt loop.
        Optionally pass argparse args to the command handler.
        """
        if cmd:
            try:
                self._handle_command(cmd, args=args)
            except GoBackToPrompt:
                pass
        while True:
            self._display_status()
            try:
                user_cmd = self.prompt_session.prompt(
                    HTML("<b><orange>msig></orange></b> Enter command (or 'help'): ")
                ).strip()
            except (EOFError, KeyboardInterrupt):
                print_formatted_text(HTML("\n<b><red>Exiting msig CLI.</red></b>"))
                break
            if not user_cmd or user_cmd.lower() in {"exit", "quit"}:
                print_formatted_text(HTML("\n<b><red>Goodbye!</red></b>"))
                break
            if user_cmd.lower() in {"help", "?"}:
                self._display_help()
                continue
            try:
                self._handle_command(user_cmd)
            except GoBackToPrompt:
                continue
            except KeyboardInterrupt:
                logger.info("Exiting interactive mode.")
                break
            except Exception as e:
                logger.error(f"An error occurred: {e}")
                continue

    def _display_status(self):
        """Display current msig CLI status and available commands."""
        print_formatted_text(HTML("\n<b><magenta>=== msig CLI ===</magenta></b>"))

        # Display current Safe instance and SafeTx status
        if self.safe_instance:
            print_formatted_text(HTML(f"<b>Safe:</b> {self.safe_instance.address}"))
        else:
            print_formatted_text(HTML("<b>Safe:</b> <grey>Not initialized</grey>"))
        if self.safe_tx:
            print_formatted_text(
                HTML(
                    f"<b>SafeTx:</b> {self.safe_tx.safe_tx_hash or '<grey>Not created</grey>'}"
                )
            )
        else:
            print_formatted_text(HTML("<b>SafeTx:</b> <grey>Not created</grey>"))

        # Display available commands
        print_formatted_text(
            HTML("<b>Available commands:</b> " + ", ".join(self.commands.keys()))
        )

    def _display_help(self):
        """Display help information for available commands."""
        print_formatted_text(HTML("\n<b>Available commands:</b>"))
        for cmd in self.commands:
            print_formatted_text(HTML(f"  <b>{cmd}</b>"))
        print_formatted_text(HTML("Type 'exit' or 'quit' to leave."))

    def _tx_builder_command(self, args=None):
        """Run the transaction builder command. Accepts optional argparse args."""
        print_formatted_text(
            HTML("\n<b><magenta>Running tx_builder command...</magenta></b>")
        )
        try:
            self.safe_tx = tx_builder.run(self.safe_instance, args=args)
        except GoBackToPrompt:
            raise

    def _tx_signer_command(self):
        """Run the transaction signer command."""
        print_formatted_text(
            HTML("<b><red>tx_signer command not implemented yet!</red></b>")
        )

    def _tx_broadcast_command(self):
        """Run the transaction broadcast command."""
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
            ethereum_client = EthereumClient(rpc_url)
            safe_address = ChecksumAddress(safe_address)
            self.safe_instance = Safe(
                address=safe_address, ethereum_client=ethereum_client
            )
            print_formatted_text(
                HTML(
                    "\n<b><green>Safe instance initialized successfully!</green></b>\n"
                )
            )
            return self.safe_instance
        except Exception as e:
            logger.error(f"Failed to initialize Safe instance: {e}")
            raise e

    def _handle_command(self, cmd: str, args=None):
        """Handle a command input by the user.

        :param cmd: The command string input by the user.
        :param args: Optional argparse args to pass to the command handler.
        """
        if cmd not in self.commands:
            print_formatted_text(HTML(f"<b><red>Unknown command: {cmd}</red></b>"))
            return
        prompt_clear()
        if cmd.startswith("tx_") and not self.safe_instance:
            print_formatted_text(
                HTML(
                    "<b><yellow>Safe instance not initialized. Please provide RPC URL and Safe address.</yellow></b>"
                )
            )
            while not self.safe_instance:
                try:
                    rpc_url = self.prompt_session.prompt(HTML("<b>RPC URL:</b> "))
                    safe_address = self.prompt_session.prompt(
                        HTML("<b>Safe address:</b> ")
                    )
                    self._initialize_safe_instance(rpc_url, safe_address)
                except (EOFError, KeyboardInterrupt):
                    print_formatted_text(
                        HTML("\n<b><red>Aborted Safe initialization.</red></b>")
                    )
                    return
        # Pass args if supported
        handler = self.commands[cmd]
        if args is not None:
            handler(args)
        else:
            handler()
