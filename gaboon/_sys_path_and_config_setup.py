from pathlib import Path
import sys
from gaboon.config import get_config
from gaboon.gaboon_account import GaboonAccount
import boa
from gaboon.logging import logger
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
    fork: bool = False,
    account: str | None = None,
    private_key: str | None = None,
    password: str | None = None,
    password_file_path: Path | None = None,
) -> None:
    if fork and account:
        raise ValueError("Cannot use --fork and --account at the same time")
    
    gab_account: GaboonAccount | None = None
    config = get_config()

    if network and not url:
        config.networks.set_active_network(network, is_fork=fork)
    if url:
        config.networks.set_active_network(url, is_fork=fork)
    
    if password_file_path is None:
        password_file_path = config.networks.get_active_network().unsafe_password_file
    
    if account is None:
        account = config.networks.get_active_network().default_account_name

    if account:
        # This will also attempt to unlock the account with a prompt
        # If no password or password file is passed
        gab_account = GaboonAccount(
            keystore_path_or_account_name=account,
            password=password,
            password_file_path=password_file_path,
        )
    if private_key:
        gab_account = GaboonAccount(
            private_key=private_key,
            password=password,
            password_file_path=password_file_path,
        )

    if gab_account:
        boa.env.add_account(gab_account, force_eoa=True)
    if boa.env.eoa is None:
        logger.warning(
            "No default EOA account found. Please add an account to the environment before attempting a transaction."
        )
