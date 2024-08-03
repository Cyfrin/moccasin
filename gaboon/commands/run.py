from typing import List, Any
import sys
from pathlib import Path
from gaboon.logging import logger
from gaboon import get_config, initialize_global_config
import importlib.util
from gaboon._sys_path_and_config_setup import (
    _add_to_sys_path,
    _setup_network_and_account_from_args,
)
from gaboon.constants.vars import CONTRACTS_FOLDER, DEFAULT_ANVIL_PRIVATE_KEY
import boa
from gaboon.gaboon_account import GaboonAccount
from argparse import Namespace

BOA_VM = "pyevm"


def main(args: Namespace) -> int:
    initialize_global_config()
    run_script(
        args.script_name_or_path,
        network=args.network,
        account=args.account,
        private_key=args.private_key,
        password=args.password,
        password_file_path=args.password_file_path,
        fork=args.fork,
        url=args.url,
    )
    return 0


def run_script(
    script_name_or_path: Path | str,
    network: str = None,
    account: str = None,
    private_key: str = None,
    password: str = None,
    password_file_path: Path = None,
    fork: bool = False,
    url: str = None,
):
    config = get_config()
    config_root = config.get_root()
    script_path: Path = get_script_path(script_name_or_path)

    # Set up the environment (add necessary paths to sys.path, etc.)
    # REVIEW: this semantics is a bit weird -- it means if you run `gab run` from some nested directory, the root directory will be in the syspath
    # TODO - what is better?
    _add_to_sys_path(config_root)
    _add_to_sys_path(config_root / CONTRACTS_FOLDER)

    # We give the user's script the module name "deploy_script_gaboon"
    spec = importlib.util.spec_from_file_location("deploy_script_gaboon", script_path)
    if spec is None:
        raise Exception(f"Cannot find script '{script_path}'")

    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise Exception(f"Cannot find a loader for '{script_path}'")

    # TODO: Is this correct putting it up here? Should it be lower?
    spec.loader.exec_module(module)

    _setup_network_and_account_from_args(
        network=network,
        url=url,
        fork=fork,
        account=account,
        private_key=private_key,
        password=password,
        password_file_path=password_file_path,
    )

    if hasattr(module, "main") and callable(module.main):
        result = module.main()
        return result
    else:
        logger.info("No main() function found. Executing script as is...")
    sys.path.pop(0)
    sys.path.pop(0)


def get_script_path(script_name_or_path: Path | str) -> Path:
    script_path = Path(script_name_or_path)
    root = get_config().get_root()

    if script_path.suffix != ".py":
        script_path = script_path.with_suffix(".py")

    if not script_path.is_absolute():
        if root not in script_path.parts:
            script_path = root / "script" / script_path
        else:
            script_path = root / script_path

    if not script_path.exists():
        logger.error(f"{script_path} not found")

    return script_path
