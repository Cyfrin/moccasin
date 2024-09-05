from pathlib import Path
from gaboon.logging import logger
from gaboon.config import get_config, initialize_global_config
import importlib.util
from gaboon._sys_path_and_config_setup import (
    _patch_sys_path,
    _setup_network_and_account_from_args,
)
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
    with _patch_sys_path([config_root, config_root / config.contracts_folder]):
        _setup_network_and_account_from_args(
            network=network,
            url=url,
            fork=fork,
            account=account,
            private_key=private_key,
            password=password,
            password_file_path=password_file_path,
        )

        # We give the user's script the module name "deploy_script_gaboon"
        spec = importlib.util.spec_from_file_location(
            "deploy_script_gaboon", script_path
        )
        if spec is None:
            raise Exception(f"Cannot find script '{script_path}'")

        if spec.loader is None:
            raise Exception(f"not a module: '{script_path}'")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # neat functionality:
        if hasattr(module, "main") and callable(module.main):
            result = module.main()
            return result


def get_script_path(script_name_or_path: Path | str) -> Path:
    script_path = Path(script_name_or_path)
    root = get_config().get_root()
    if script_path.suffix != ".py":
        script_path = script_path.with_suffix(".py")

    if not script_path.is_absolute():
        if "script" not in script_path.parts:
            script_path = root / "script" / script_path
        else:
            script_path = root / script_path

    if not script_path.exists():
        logger.error(f"{script_path} not found")

    return script_path
