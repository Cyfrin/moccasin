from pathlib import Path
import sys
from gaboon.config import get_config
from gaboon.gaboon_account import GaboonAccount
import boa
from gaboon.logging import logger
import contextmanager


@contextlib.contextmanager
def _patch_sys_path(paths: list[str | Path]) -> None:
    paths = [str(p) for p in paths]
    anchor = sys.path
    try:
        # add these with highest precedence -- conflicts should prefer user modules/code
        sys.path = paths + sys.path
        yield
    finally:
        sys.path = anchor

def _setup_network_and_account_from_args(
    network: str = None,
    url: str = None,
    fork: bool = None,
    account: str = None,
    private_key: str = None,
    password: str = None,
    password_file_path: Path = None,
) -> None:
    config = get_config()
    if network and not url:
        config.networks.set_active_network(network, is_fork=fork)
    if url:
        config.networks.set_active_network(url, is_fork=fork)
    if account:
        # This will also attempt to unlock the account
        account = GaboonAccount(
            keystore_path_or_account_name=account,
            password=password,
            password_file_path=password_file_path,
        )
    if private_key:
        account = GaboonAccount(
            private_key=private_key,
            password=password,
            password_file_path=password_file_path,
        )
    if fork and account:
        raise ValueError("Cannot use --fork and --account at the same time")
    if account:
        boa.env.add_account(account, force_eoa=True)
        if boa.env.eoa is None:
            logger.warning(
                "No default EOA account found. Please add an account to the environment before attempting a transaction."
            )
