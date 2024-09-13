import json
from pathlib import Path
import boa
from argparse import Namespace
import os
from moccasin.constants.vars import (
    DEFAULT_API_KEY_ENV_VAR,
    DEFAULT_NETWORKS_BY_NAME,
    DEFAULT_NETWORKS_BY_CHAIN_ID,
)
from moccasin.logging import logger, set_log_level
from moccasin.config import get_config


def main(args: Namespace) -> int:
    if args.explorer_command == "list":
        list_supported_explorers(args.by_id, json=args.json)
    elif args.explorer_command == "get":
        boa_get_abi_from_explorer(
            args.address,
            name=args.name,
            uri=args.uri,
            api_key=args.api_key,
            save_abi_path=args.save_abi_path,
            ignore_config=args.ignore_config,
            chain=args.chain,
            network=args.network,
        )
    else:
        logger.warning(f"Unknown explorer command: {args.explorer_command}")
    return 0


def boa_get_abi_from_explorer(
    address: str,
    name: str | None = None,
    uri: str | None = None,
    api_key: str | None = None,
    save_abi_path: str | None = None,
    ignore_config: bool = False,
    chain: str | None = None,
    network: str | None = None,
    quiet: bool = False,  # This is for when this function is used as a library
) -> list:
    if quiet:
        set_log_level(quiet=True)

    if not api_key:
        api_key = os.getenv(DEFAULT_API_KEY_ENV_VAR)

    if chain is not None:
        ignore_config = True
        if chain.isdigit():
            chain_id = int(chain)
            uri = DEFAULT_NETWORKS_BY_CHAIN_ID.get(chain_id, {}).get("explorer")
        else:
            uri = DEFAULT_NETWORKS_BY_NAME.get(chain, {}).get("explorer")

    if not ignore_config:
        config = get_config()
        if network:
            config.networks.set_active_network(network)
        active_network = config.get_active_network()
        if not uri:
            uri = active_network.explorer_uri
        if not api_key:
            api_key = active_network.explorer_api_key
        if not save_abi_path:
            save_abi_path = active_network.save_abi_path

    if not api_key:
        raise ValueError(
            f"No API key provided. Please provide one in the command line with --api-key or set the environment variable:\n{DEFAULT_API_KEY_ENV_VAR}"
        )

    if save_abi_path and not name:
        raise ValueError(
            "If you provide a save path, you must also provide a name for the ABI file via --save-abi-path."
        )

    abi: list = []
    with boa.set_etherscan(uri, api_key=api_key):
        explorer = boa.explorer.get_etherscan()
        abi = explorer.fetch_abi(address)
        if len(abi) == 0:
            logger.warning(f"No ABI found for address: {address}")
            return abi

    if save_abi_path:
        name = str(name)
        if not name.endswith(".json"):
            name = name + ".json"
        resolved_path = Path(save_abi_path).expanduser().resolve().joinpath(name)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        with open(resolved_path, "w") as f:
            logger.info(f"Saving ABI to {save_abi_path}/{name}...")
            json.dump(abi, f, indent=4)
            logger.info("ABI saved")
    else:
        logger.info(abi)
    return abi


def list_supported_explorers(by_id: bool, json: bool = False) -> dict:
    logger.info("Supported explorers:")
    if by_id:
        if json:
            logger.info(DEFAULT_NETWORKS_BY_CHAIN_ID)
            return DEFAULT_NETWORKS_BY_CHAIN_ID
        for chain_id in DEFAULT_NETWORKS_BY_CHAIN_ID:
            logger.info(f"- {chain_id}:")
            logger.info(f"  - {DEFAULT_NETWORKS_BY_CHAIN_ID[chain_id]}")
        return DEFAULT_NETWORKS_BY_CHAIN_ID

    if json:
        logger.info(DEFAULT_NETWORKS_BY_NAME)
    else:
        for chain_name in DEFAULT_NETWORKS_BY_NAME:
            logger.info(f"- {chain_name}:")
            logger.info(f"  - {DEFAULT_NETWORKS_BY_NAME[chain_name]}")
    return DEFAULT_NETWORKS_BY_NAME
