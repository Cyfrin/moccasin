import contextlib
import sys
from pathlib import Path
from typing import Iterator, List

import boa

from moccasin.config import Network, get_config, Config
from moccasin.constants.vars import ERA_DEFAULT_PRIVATE_KEY, ERAVM
from moccasin.logging import logger
from moccasin.moccasin_account import MoccasinAccount
from moccasin.constants.vars import PYPI, GITHUB


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


@contextlib.contextmanager
def _patch_sys_path(paths: List[str | Path]) -> Iterator[None]:
    str_paths = [str(p) for p in paths]
    anchor = sys.path
    try:
        # add these with highest precedence -- conflicts should prefer user modules/code
        sys.path = str_paths + sys.path
        yield
    finally:
        sys.path = anchor


def _setup_network_and_account_from_args_and_cli(
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

    if network is None:
        network = config.default_network

    # 1. Update the network with the CLI values
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
    )

    active_network: Network = config.get_active_network()
    if active_network is None:
        raise ValueError("No active network set. Please set a network.")

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
        if active_network.is_fork:
            boa.env.eoa = mox_account.address
        else:
            boa.env.add_account(mox_account, force_eoa=True)

    if not mox_account and active_network.name is ERAVM:
        boa.env.add_account(MoccasinAccount(private_key=ERA_DEFAULT_PRIVATE_KEY))

    # Check if it's a fork, pyevm, or eravm
    if not active_network.is_testing_network():
        if boa.env.eoa is None:
            logger.warning(
                "No default EOA account found. Please add an account to the environment before attempting a transaction."
            )
