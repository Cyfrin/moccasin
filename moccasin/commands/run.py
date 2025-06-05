import contextlib
import importlib.util
from argparse import Namespace
from pathlib import Path

from moccasin._sys_path_and_config_setup import (
    _patch_sys_path,
    _setup_network_and_account_from_config_and_cli,
    get_sys_paths_list,
    setup_network_and_account_for_metamask_ui,
)
from moccasin.commands.install import mox_install
from moccasin.config import get_config, initialize_global_config
from moccasin.logging import logger, set_log_level


def main(args: Namespace) -> int:
    initialize_global_config()

    if not args.no_install:
        mox_install(config=get_config(), quiet=True, override_logger=True)
    set_log_level(quiet=args.quiet, debug=args.debug)

    run_script(
        args.script_name_or_path,
        network=args.network,
        account=args.account,
        private_key=args.private_key,
        password=args.password,
        password_file_path=args.password_file_path,
        fork=args.fork,
        url=args.url,
        prompt_live=args.prompt_live,
        db_path=args.db_path,
        prompt_metamask=args.prompt_metamask,
    )
    return 0


def run_script(
    script_name_or_path: Path | str,
    network: str = None,
    account: str = None,
    private_key: str = None,
    password: str = None,  # This parameter is no longer used in the context manager
    password_file_path: Path = None,
    fork: bool = False,
    url: str = None,
    prompt_live: bool = None,
    db_path: str = None,
    prompt_metamask: bool = False,  # This controls which setup is used
):
    config = get_config()
    script_path: Path = get_script_path(script_name_or_path)

    # Use a variable to hold the context manager based on the flag
    # This pattern allows you to choose the context at runtime.
    setup_context_manager = None

    if prompt_metamask:
        # If MetaMask is prompted, use the new context manager
        setup_context_manager = setup_network_and_account_for_metamask_ui(
            network=network,
            url=url,
            fork=fork,
            account=account,
            private_key=private_key,
            password_file_path=password_file_path,
            prompt_live=prompt_live,
            explorer_uri=None,  # Ensure these are passed if needed, or set defaults
            explorer_api_key=None,  # Ensure these are passed if needed, or set defaults
            db_path=db_path,
            save_to_db=None,  # Ensure this is passed if needed, or set defaults
        )
    else:
        # If not MetaMask, use the original setup function (which is NOT a context manager)
        # We wrap it in a dummy context manager to fit the 'with' statement.
        # This is a common pattern for conditional context managers.
        @contextlib.contextmanager
        def _dummy_context_manager():
            _setup_network_and_account_from_config_and_cli(
                network=network,
                url=url,
                fork=fork,
                account=account,
                private_key=private_key,
                password=password,  # Password is used in the original function
                password_file_path=password_file_path,
                prompt_live=prompt_live,
                db_path=db_path,
            )
            yield  # No specific cleanup needed by this dummy context manager

        setup_context_manager = _dummy_context_manager()

    # Set up the environment (add necessary paths to sys.path, etc.)
    with _patch_sys_path(get_sys_paths_list(config)):
        # Now, use the selected context manager
        with setup_context_manager:
            # We give the user's script the module name "deploy_script_moccasin"
            spec = importlib.util.spec_from_file_location(
                "deploy_script_moccasin", script_path
            )
            if spec is None:
                raise Exception(f"Cannot find script '{script_path}'")

            if spec.loader is None:
                raise Exception(f"not a module: '{script_path}'")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # neat functionality:
            if hasattr(module, "moccasin_main") and callable(module.moccasin_main):
                result = module.moccasin_main()
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
