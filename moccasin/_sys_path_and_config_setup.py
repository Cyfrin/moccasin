from pathlib import Path
import sys
from moccasin.config import get_config
from moccasin.moccasin_account import MoccasinAccount
import boa
from moccasin.logging import logger
import contextlib
from typing import Iterator, List


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


def _setup_network_and_account_from_args(
    network: str = None,
    url: str = None,
    fork: bool | None = None,
    account: str | None = None,
    private_key: str | None = None,
    password: str | None = None,
    password_file_path: Path | None = None,
    prompt_live: bool | None = None,
):
    mox_account: MoccasinAccount | None = None
    config = get_config()

    # Specifically a CLI check
    if fork and account:
        raise ValueError("Cannot use --fork and --account at the same time")

    # Setup Network
    if network and not url:
        config.networks.set_active_network(network, is_fork=fork)
    if url:
        config.networks.set_active_network(url, is_fork=fork)

    # Update parameters if not provided in the CLI
    if fork is None:
        fork = config.get_active_network().is_fork
    if password_file_path is None:
        password_file_path = config.networks.get_active_network().unsafe_password_file
    if account is None:
        account = config.networks.get_active_network().default_account_name
    if prompt_live is None:
        prompt_live = config.get_active_network().prompt_live

    if prompt_live:
        if not fork:
            response = input(
                "The transactions run on this will actually be broadcast/transmitted, spending gas associated with your account. Are you sure you wish to continue?\nType 'y' or 'Y' and hit 'ENTER' or 'RETURN' to continue:\n"
            )
            if response.lower() != "y":
                logger.info("Operation cancelled.")
                sys.exit(0)

    if account:
        # This will also attempt to unlock the account with a prompt
        # If no password or password file is passed
        mox_account = MoccasinAccount(
            keystore_path_or_account_name=account,
            password=password,
            password_file_path=password_file_path,
        )
    if private_key:
        mox_account = MoccasinAccount(
            private_key=private_key,
            password=password,
            password_file_path=password_file_path,
        )

    if mox_account:
        if fork:
            boa.env.eoa = mox_account.address
        else:
            boa.env.add_account(mox_account, force_eoa=True)
    if boa.env.eoa is None:
        logger.warning(
            "No default EOA account found. Please add an account to the environment before attempting a transaction."
        )
