import contextlib
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List

import boa
from boa.util.abi import Address

from moccasin.config import Config, Network, get_config
from moccasin.constants.vars import (
    DEFAULT_ANVIL_PRIVATE_KEY,
    ERAVM,
    GITHUB,
    PYEVM,
    PYPI,
    STARTING_BOA_BALANCE,
)
from moccasin.logging import logger
from moccasin.metamask_cli_integration import (
    MetaMaskAccount,
    start_metamask_ui_server,
    stop_metamask_ui_server,
)
from moccasin.moccasin_account import MoccasinAccount


def get_sys_paths_list(config: Config) -> List[Path]:
    config_root = config.get_root()
    config_contracts = config_root.joinpath(config.contracts_folder)

    base_install_path = config_root.joinpath(config.lib_folder)

    # REVIEW: We could also look into the versions.toml file and add those to the search path too
    # This way, we could make the imports even cleaner
    github_dependencies = base_install_path.joinpath(GITHUB)
    pypi_dependencies = base_install_path.joinpath(PYPI)

    return [
        config_root,
        config_contracts,
        github_dependencies,
        pypi_dependencies,
        base_install_path,
    ]


def _set_sys_path(paths: List[Path]):
    str_paths = [str(p) for p in paths]
    anchor2 = os.environ.get("PYTHONPATH")
    python_path = anchor2
    if python_path is None:
        python_path = ":".join(str_paths)
    else:
        python_path = ":".join([*str_paths, python_path])
    os.environ["PYTHONPATH"] = python_path
    # add these with highest precedence -- conflicts should prefer user modules/code
    sys.path = str_paths + sys.path


@contextlib.contextmanager
def _patch_sys_path(paths: List[Path]) -> Iterator[None]:
    str_paths = [str(p) for p in paths]
    anchor = sys.path
    anchor2 = os.environ.get("PYTHONPATH")
    python_path = anchor2
    if python_path is None:
        python_path = ":".join(str_paths)
    else:
        python_path = ":".join([*str_paths, python_path])
    os.environ["PYTHONPATH"] = python_path
    try:
        # add these with highest precedence -- conflicts should prefer user modules/code
        sys.path = str_paths + sys.path
        yield
    finally:
        sys.path = anchor
        if anchor2 is None:
            del os.environ["PYTHONPATH"]
        else:
            os.environ["PYTHONPATH"] = anchor2


# REVIEW: Might be best to just set this as **kwargs
def _get_set_active_network_from_cli_and_config(
    config: Config,
    network: str | None = None,
    url: str | None = None,
    fork: bool | None = None,
    account: str | None = None,
    password_file_path: Path | None = None,
    prompt_live: bool | None = None,
    explorer_uri: str | None = None,
    explorer_api_key: str | None = None,
    db_path: str | None = None,
    save_to_db: bool | None = None,
) -> Network:
    if network is None:
        network = config.default_network

    if fork is not None and isinstance(fork, str):
        if fork.lower().strip() == "false":
            fork = False

    config.set_active_network(
        network,
        is_fork=fork,
        url=url,
        default_account_name=account,
        # private_key=private_key, # No private key in networks
        # password=password, # No password in networks
        password_file_path=password_file_path,
        prompt_live=prompt_live,
        explorer_uri=explorer_uri,
        explorer_api_key=explorer_api_key,
        db_path=db_path,
        save_to_db=save_to_db,
    )

    active_network: Network = config.get_active_network()
    logger.debug(f"Active network set to: {active_network.name}")
    if active_network is None:
        raise ValueError("No active network set. Please set a valid network.")
    return active_network


def _setup_network_and_account_from_config_and_cli(
    network: str = None,
    url: str = None,
    fork: bool | None = None,
    account: str | None = None,
    private_key: str | None = None,
    password: str | None = None,
    password_file_path: Path | None = None,
    prompt_live: bool | None = None,
    explorer_uri: str | None = None,
    explorer_api_key: str | None = None,
    db_path: str | None = None,
    save_to_db: bool | None = None,
):
    """All the network and account logic in the function parameters are from the CLI.
    We will use the order of operations to setup the network:

        1. scripts (which, we don't touch here)
        2. CLI
        3. Config
        4. Default Values

    All the values passed into this function come from the CLI.
    """
    if account is not None and private_key is not None:
        raise ValueError("Cannot set both account and private key in the CLI!")

    mox_account: MoccasinAccount | None = None
    config = get_config()

    # 1. Update the network with the CLI values
    active_network = _get_set_active_network_from_cli_and_config(
        config,
        network,
        url,
        fork,
        account,
        password_file_path,
        prompt_live,
        explorer_uri,
        explorer_api_key,
        db_path,
        save_to_db,
    )

    # 2. Update and set account
    if active_network.prompt_live:
        if not fork:
            response = input(
                "The transactions run on this will actually be broadcast/transmitted, spending gas associated with your account. Are you sure you wish to continue?\nType 'y' or 'Y' and hit 'ENTER' or 'RETURN' to continue:\n"
            )
            if response.lower() != "y":
                logger.info("Operation cancelled.")
                sys.exit(0)

    if active_network.default_account_name and private_key is None:
        # This will also attempt to unlock the account with a prompt
        # If no password or password file is passed
        mox_account = MoccasinAccount(
            keystore_path_or_account_name=active_network.default_account_name,
            password=password,
            password_file_path=active_network.unsafe_password_file,
        )

    # Private key overrides the default account
    if private_key:
        mox_account = MoccasinAccount(
            private_key=private_key,
            password=password,
            password_file_path=active_network.unsafe_password_file,
        )

    if mox_account:
        if active_network.is_local_or_forked_network() and not active_network.is_zksync:
            boa.env.eoa = mox_account.address
        else:
            # @dev boa_zksync always request to use add_account
            boa.env.add_account(mox_account, force_eoa=True)

    # Add default account anvil-zksync if not provided
    if (
        not mox_account
        and active_network.is_zksync
        and active_network.is_local_or_forked_network()
    ):
        boa.env.add_account(MoccasinAccount(private_key=DEFAULT_ANVIL_PRIVATE_KEY))

    # Check if it's a fork, pyevm, or eravm
    if not active_network.is_local_or_forked_network():
        if boa.env.eoa is None:
            logger.warning(
                "No default EOA account found. Please add an account to the environment before attempting a transaction."
            )

    if isinstance(boa.env.eoa, Address) and active_network.is_local_or_forked_network():
        boa.env.set_balance(boa.env.eoa, STARTING_BOA_BALANCE)


# @dev contextmanager allows to act as a robust initializer and finalizer
# ensuring that external resources like the MetaMask UI server are properly managed.
# @dev separated from _setup_network_and_account_from_config_and_cli to avoid
# unwanted side effects in other CLI commands that might use this function.
@contextlib.contextmanager
def setup_network_and_account_for_metamask_ui(
    network: str | None = None,
    url: str | None = None,
    fork: bool | None = None,
    account: str | None = None,
    private_key: str | None = None,
    password_file_path: Path | None = None,
    prompt_live: bool | None = None,
    explorer_uri: str | None = None,
    explorer_api_key: str | None = None,
    db_path: str | None = None,
    save_to_db: bool | None = None,
):
    """Context manager to set up the network and account for MetaMask UI integration.

    This function initializes the network and account based on CLI parameters and config,
    and starts the MetaMask UI server for user interaction.
    It ensures that the environment is properly configured for MetaMask integration,
    and cleans up resources after use.

    :param network: The name of the network to set as active.
    :param url: The URL of the network to connect to.
    :param fork: Whether to use a forked network.
    :param account: The account name to use for the network.
    :param private_key: The private key to use for the account.
    :param password_file_path: Path to the password file for the account.
    :param prompt_live: Whether to prompt the user for confirmation on live networks.
    :param explorer_uri: The URI of the blockchain explorer.
    :param explorer_api_key: The API key for the blockchain explorer.
    :param db_path: Path to the database for storing network data.
    :param save_to_db: Whether to save network data to the database.
    :raises ValueError: If both account and private key are provided.
    :yield: Yields control to the calling script after setting up the environment.
    """
    if account is not None and private_key is not None:
        raise ValueError("Cannot set both account and private key in the CLI!")

    config = get_config()
    server_control = None  # Initialize server_control to None

    try:
        # Step 1: Set active network
        active_network = _get_set_active_network_from_cli_and_config(
            config,
            network,
            url,
            fork,
            account,
            password_file_path,
            prompt_live,
            explorer_uri,
            explorer_api_key,
            db_path,
            save_to_db,
        )

        # Step 2: Handle MetaMask UI integration
        # Check if the active network is compatible with MetaMask UI
        if active_network.name in [ERAVM, PYEVM]:
            logger.info(
                f"MetaMask UI mode is not supported for {active_network.name} networks."
            )
            sys.exit(0)

        # Proceed with MetaMask UI integration
        logger.info("MetaMask UI mode enabled. Initiating browser connection...")

        # Prepare network details to pass to the frontend
        boa_network_details: Dict[str, Any] = {
            "chainId": str(active_network.chain_id)
            if active_network.chain_id
            else "unknown",
            "rpcUrl": active_network.url or "unknown",
            "networkName": active_network.name.capitalize()
            if active_network.name
            else "Boa Network",
        }

        server_control = start_metamask_ui_server(
            boa_network_details
        )  # Pass network details

        # Poll for an account with balance
        logger.info("Checking connected account balance...")
        max_attempts = 150  # 5 minutes total (2 second intervals)
        attempts = 0

        while attempts < max_attempts:
            current_balance = boa.env.get_balance(
                server_control.connected_account_address
            )

            if current_balance > 0:
                server_control.account_status = {
                    "ok": True,
                    "message": "Connected wallet has gas. Proceeding with transaction.",
                    "current_address": str(server_control.connected_account_address),
                }
                logger.info(
                    f"Account {server_control.connected_account_address} has balance: {current_balance}"
                )
                break

            # Update the account status to show zero balance
            server_control.account_status = {
                "ok": False,
                "error": "zero_balance",
                "message": "Connected wallet has 0 gas. Please change to an account with funds.",
                "current_address": str(server_control.connected_account_address),
            }

            if attempts == 0:  # Only log once
                logger.warning(
                    f"Connected account {server_control.connected_account_address} has zero balance. Waiting for account with funds..."
                )

            # Wait for 2 seconds before checking again
            time.sleep(2)
            attempts += 1

            # Check if account was changed (clear and wait for new connection)
            if server_control.connected_account_event.wait(timeout=0.1):
                # Account was changed, reset the event and check new balance
                server_control.connected_account_event.clear()
                logger.info(
                    f"Account changed to: {server_control.connected_account_address}"
                )
                attempts = 0  # Reset attempts for new account

        if current_balance <= 0:
            logger.error("No account with balance was connected within timeout period.")
            raise TimeoutError(
                "No account with balance connected. Please use an account with funds."
            )

        metamask_account_instance = MetaMaskAccount(
            str(server_control.connected_account_address)
        )

        # Ensure the MetaMask account is added to the boa environment
        if active_network.is_local_or_forked_network():
            boa.env.eoa = metamask_account_instance.address
        else:
            boa.env.add_account(
                metamask_account_instance, force_eoa=True
            )  # Live networks use boa's account management

        logger.info(f"Boa environment configured with MetaMask account: {boa.env.eoa}")

        yield  # Yield control to the calling script

    finally:
        # Step 3: Cleanup
        if server_control:
            stop_metamask_ui_server(server_control)  # Stop the server and browser
        logger.info("MetaMask UI integration cleanup complete.")
