import sys
from argparse import Namespace
from pathlib import Path
from typing import List

# We don't need to import it, pytest handles that below
# from moccasin import plugin
import pytest

from moccasin._sys_path_and_config_setup import (
    _patch_sys_path,
    _setup_network_and_account_from_config_and_cli,
    get_sys_paths_list,
)
from moccasin.config import Config, get_config, initialize_global_config
from moccasin.constants.vars import TESTS_FOLDER

HYPOTHESIS_ARGS: list[str] = ["hypothesis-seed"]

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
    "tb",
]


def main(args: Namespace) -> int:
    initialize_global_config()
    pytest_args = []

    # This is not in PYTEST_ARGS
    if "coverage" in args and args.coverage:
        pytest_args.extend(["--cov=.", "--cov-branch"])

    # Handle xdist arguments
    if args.numprocesses is not None:
        pytest_args.extend(["-n", args.numprocesses])
    if args.dist is not None:
        pytest_args.extend(["--dist", args.dist])
    if args.verbose is not None:
        pytest_args.extend(["-" + "v" * args.verbose])

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
        pytest_args,
        network=args.network,
        fork=args.fork,
        prompt_live=args.prompt_live,
        db_path=args.db_path,
        save_to_db=args.save_to_db,
        account=args.account,
        private_key=args.private_key,
        password=args.password,
        password_file_path=args.password_file_path,
        url=args.url,
    )


def _run_project_tests(
    pytest_args: List[str],
    network: str = None,
    account: str = None,
    private_key: str = None,
    password: str = None,
    password_file_path: Path = None,
    fork: bool = False,
    prompt_live: bool = None,
    db_path: str = None,
    save_to_db: bool = None,
    config: Config = None,
    url: str = None,
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
            url=url,
            fork=fork,
            account=account,
            private_key=private_key,
            password=password,
            password_file_path=password_file_path,
            prompt_live=prompt_live,
            db_path=db_path,
            save_to_db=save_to_db,
        )

        pytest_args.extend(["-p", "moccasin.plugin"])
        pytest_args = [
            "--confcutdir",
            str(config_root),
            "--rootdir",
            str(config_root),
        ] + pytest_args
        return_code: int = pytest.main(["--assert=plain"] + pytest_args)
        if return_code:
            sys.exit(return_code)
