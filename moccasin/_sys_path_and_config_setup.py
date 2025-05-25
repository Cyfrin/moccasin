import contextlib
import os
import sys
from pathlib import Path
from typing import Iterator, List

import boa
from boa.util.abi import Address

from moccasin.config import Config, Network, get_config
from moccasin.constants.vars import (
    ERA_DEFAULT_PRIVATE_KEY,
    ERAVM,
    GITHUB,
    PYPI,
    STARTING_BOA_BALANCE,
)
from moccasin.logging import logger
from moccasin.moccasin_account import MoccasinAccount
from moccasin.metamask_integration import (
    start_metamask_ui_server,
    stop_metamask_ui_server,
    MetaMaskAccount,
)


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
    network: str = None,
    url: str = None,
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


# @dev allows _setup_network_and_account_from_config_and_cli to act as a robust initializer
# and finalizer for your Moccasin script's environment, ensuring that
# external resources like the MetaMask UI server are properly managed.
@contextlib.contextmanager
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
    prompt_metamask: bool = False,
):
    """
    All the network and account logic in the function parameters are from the CLI.
    This function sets up the network and account for the script's execution.
    """
    if account is not None and private_key is not None:
        raise ValueError("Cannot set both account and private key in the CLI!")

    mox_account: MoccasinAccount | None = None
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
        if prompt_metamask:
            logger.info("MetaMask UI mode enabled. Initiating browser connection...")
            server_control = start_metamask_ui_server()  # Start server and browser

            # The connected_account_address from control is already a boa.Address object.
            # Use it to get the checksum string for MetaMaskAccount init
            metamask_account_instance = MetaMaskAccount(
                str(server_control.connected_account_address)
            )

            # 1. Set boa.env.eoa to the actual Address (boa.Address) of the MetaMask account.
            #    This is what Boa expects for its 'sender' logic.
            boa.env.eoa = server_control.connected_account_address

            # 2. Register our custom MetaMaskAccount instance with the current network's accounts.
            #    Access boa.env.current_network to get the NetworkEnv instance.
            boa.env.current_network.accounts[
                server_control.connected_account_address
            ] = metamask_account_instance

            logger.info(
                f"Boa environment configured with MetaMask account: {boa.env.eoa}"
            )

        # Step 3: Handle traditional Moccasin accounts if not using MetaMask UI
        else:
            if active_network.prompt_live:
                if not fork:
                    response = input(
                        "The transactions run on this will actually be broadcast/transmitted, spending gas associated with your account. Are you sure you wish to continue?\nType 'y' or 'Y' and hit 'ENTER' or 'RETURN' to continue:\n"
                    )
                    if response.lower() != "y":
                        logger.info("Operation cancelled.")
                        sys.exit(0)

            if active_network.default_account_name and private_key is None:
                mox_account = MoccasinAccount(
                    keystore_path_or_account_name=active_network.default_account_name,
                    password=password,
                    password_file_path=active_network.unsafe_password_file,
                )

            if private_key:
                mox_account = MoccasinAccount(
                    private_key=private_key,
                    password=password,
                    password_file_path=active_network.unsafe_password_file,
                )

            if mox_account:
                if active_network.is_local_or_forked_network():
                    boa.env.eoa = (
                        mox_account.address
                    )  # Local/forked networks use address as EOA directly in boa
                else:
                    boa.env.add_account(
                        mox_account, force_eoa=True
                    )  # Live networks use boa's account management

            if not mox_account and active_network.name is ERAVM:
                # Add default ERAVM account if no other account specified
                boa.env.add_account(
                    MoccasinAccount(private_key=ERA_DEFAULT_PRIVATE_KEY)
                )

            if not active_network.is_local_or_forked_network():
                if boa.env.eoa is None:
                    logger.warning(
                        "No default EOA account found. Please add an account to the environment before attempting a transaction."
                    )

            # For local/forked networks, ensure EOA has balance
            if (
                isinstance(boa.env.eoa, Address)
                and active_network.is_local_or_forked_network()
            ):
                boa.env.set_balance(boa.env.eoa, STARTING_BOA_BALANCE)

        yield  # Yield control to the calling script

    finally:
        # Step 4: Cleanup
        if prompt_metamask:
            # Removed remove_boa_patch()
            if server_control:
                stop_metamask_ui_server(server_control)  # Stop the server and browser
            logger.info("MetaMask UI integration cleanup complete.")
