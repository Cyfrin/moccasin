import sys
from argparse import Namespace
from pathlib import Path
from typing import List

import pytest

from moccasin._sys_path_and_config_setup import (
    _patch_sys_path,
    _setup_network_and_account_from_config_and_cli,
    get_sys_paths_list,
)
from moccasin.config import Config, get_config, initialize_global_config
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
        if getattr(args, attr_name, None) is not None:
            value = getattr(args, attr_name)
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
    return _run_project_tests(
        pytest_args, network=args.network, fork=args.fork, prompt_live=args.prompt_live
    )


def _run_project_tests(
    pytest_args: List[str],
    network: str = None,
    fork: bool = False,
    prompt_live: bool = None,
    config: Config = None,
):
    if config is None:
        config = get_config()
    config_root = config.get_root()
    test_path = config_root.joinpath(TESTS_FOLDER)

    if "cov-config" not in pytest_args:
        if config.cov_config:
            pytest_args.extend(["--cov-config", str(config.cov_config)])

    list_of_paths: list[Path] = get_sys_paths_list(config)
    list_of_paths.append(test_path)

    with _patch_sys_path(list_of_paths):
        _setup_network_and_account_from_config_and_cli(
            network=network,
            url=None,
            fork=fork,
            account=None,
            private_key=None,
            password=None,
            password_file_path=None,
            prompt_live=prompt_live,
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
