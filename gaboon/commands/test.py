from typing import List
from gaboon.config import initialize_global_config, get_config
from gaboon._sys_path_and_config_setup import (
    _patch_sys_path,
    _setup_network_and_account_from_args,
)
import pytest
import sys
from argparse import Namespace

PYTEST_ARGS: list[str] = [
    "file_or_dir",
    "k",
    "m",
    "x",
    "s",
    "exitfirst",
    "capture",
    "lf",
    "last-failed",
    "cache-clear",
    "disable-warnings",
    "disable-pytest-warnings",
    "full-trace",
    "pdb",
]


def main(args: Namespace) -> int:
    initialize_global_config()
    pytest_args = []
    for arg in PYTEST_ARGS:
        if hasattr(args, arg):
            value = getattr(args, arg)
            if value is not None:
                if arg == "file_or_dir":
                    pytest_args.append(str(value))
                elif arg == "coverage":
                    pytest_args.append("--cov=")
                else:
                    option_prefix = "-" if len(arg) == 1 else "--"
                    option = f"{option_prefix}{arg}"

                    if isinstance(value, bool):
                        if value:
                            pytest_args.append(option)
                    elif isinstance(value, list):
                        for item in value:
                            pytest_args.extend([option, str(item)])
                    else:
                        pytest_args.extend([option, str(value)])
    return _run_project_tests(pytest_args, network=args.network, fork=args.fork)


def _run_project_tests(pytest_args: List[str], network: str = None, fork: bool = False):
    config = get_config()
    config_root = config.get_root()
    test_path = "test"

    with _patch_sys_path([config_root, config_root / test_path]):
        _setup_network_and_account_from_args(
            network=network,
            url=None,
            fork=fork,
            account=None,
            private_key=None,
            password=None,
            password_file_path=None,
        )
        return_code: int = pytest.main(["--assert=plain"] + pytest_args)
        if return_code:
            sys.exit(return_code)
