from argparse import Namespace

from moccasin._sys_path_and_config_setup import (
    _patch_sys_path,
    _setup_network_and_account_from_args_and_cli,
)
from moccasin.config import get_config, initialize_global_config
from moccasin.logging import logger


def main(args: Namespace) -> int:
    initialize_global_config()
    config_contracts = get_config().contracts_folder
    config_root = get_config().get_root()

    # Set up the environment (add necessary paths to sys.path, etc.)
    with _patch_sys_path([config_root, config_root / config_contracts]):
        _setup_network_and_account_from_args_and_cli(
            network=args.network,
            url=args.url,
            fork=args.fork,
            account=args.account,
            private_key=args.private_key,
            password=args.password,
            password_file_path=args.password_file_path,
            prompt_live=args.prompt_live,
        )
        config = get_config()
        active_network = config.get_active_network()
        deployed_contract = active_network.get_or_deploy_contract(
            args.contract_name, force_deploy=True
        )
        logger.info(
            f"Deployed contract {args.contract_name} on {active_network.name} to {deployed_contract.address}"
        )
    return 0
