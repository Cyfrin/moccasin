from argparse import Namespace

from eth_typing import URI
from prompt_toolkit import HTML, print_formatted_text

from moccasin._sys_path_and_config_setup import (
    _patch_sys_path,
    _setup_network_and_account_from_config_and_cli,
    get_sys_paths_list,
)
from moccasin.config import initialize_global_config, get_config
from moccasin.logging import set_log_level

from safe_eth.eth import EthereumClient


# --- Main Function ---
def main(args: Namespace) -> int:
    """Main entry point for the msig CLI."""
    # Initialize global configuration without requiring a TOML file
    config = initialize_global_config(is_default_project=args.with_project_toml)
    set_log_level(quiet=args.quiet, debug=args.debug)

    with _patch_sys_path(get_sys_paths_list(config)):
        _setup_network_and_account_from_config_and_cli(
            network=args.network,
            url=args.url,
            fork=args.fork,
            account=args.account,
            private_key=args.private_key,
            password=args.password,
            password_file_path=args.password_file_path,
            prompt_live=args.prompt_live,
        )
        # @TODO prompt for Metamask UI setup later

        # Initialize Ethereum client
        config = get_config()
        ethereum_client = EthereumClient(URI(config.get_active_network().url))

        # @TOCONTINUE

        # Handle the msig command
        msig_command = args.msig_command

        if msig_command == "tx_build":
            return tx_build(args)

        print_formatted_text(
            HTML("<b><green>msig CLI completed successfully.</green></b>")
        )
        # Return 0 for successful completion
        print_formatted_text(HTML("<b><cyan>Shutting down msig CLI...</cyan></b>"))
    return 0
