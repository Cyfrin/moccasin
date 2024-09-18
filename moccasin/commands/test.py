from typing import List
from moccasin.config import initialize_global_config, get_config
from moccasin._sys_path_and_config_setup import (
    _patch_sys_path,
    _setup_network_and_account_from_args,
)
import pytest
import sys
from argparse import Namespace

from moccasin.constants.vars import TESTS_FOLDER

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
    "gas-profile",
    # Coverage options
    "cov",
    "cov-report",
    "cov-config",
    "no-cov-on-fail",
    "no-cov",
    "cov-reset",
    "cov-fail-under",
    "cov-append",
    "cov-branch",
    "cov-context",
]


def main(args: Namespace) -> int:
    initialize_global_config()
    pytest_args = []

    # This is not in PYTEST_ARGS
    if "coverage" in args and args.coverage:
        pytest_args.extend(["--cov=.", "--cov-branch"])

    for arg in PYTEST_ARGS:
        attr_name = arg.replace("-", "_")
        if hasattr(args, attr_name):
            value = getattr(args, attr_name)
            if value is not None:
                if arg == "file_or_dir":
                    pytest_args.append(str(value))
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
    test_path = TESTS_FOLDER

    if "cov-config" not in pytest_args:
        if config.cov_config:
            pytest_args.extend(["--cov-config", str(config.cov_config)])

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

        pytest_args = [
            "--confcutdir",
            str(config_root),
            "--rootdir",
            str(config_root),
        ] + pytest_args
        return_code: int = pytest.main(["--assert=plain"] + pytest_args)
        if return_code:
            sys.exit(return_code)
