import json
import os
from argparse import Namespace
from pathlib import Path
from typing import cast

import boa

from moccasin.config import Network, get_or_initialize_config
from moccasin.constants.vars import (
    DEFAULT_API_KEY_ENV_VAR,
    DEFAULT_NETWORKS_BY_CHAIN_ID,
    DEFAULT_NETWORKS_BY_NAME,
)
from moccasin.logging import logger, set_log_level

ALIAS_TO_COMMAND = {"get": "fetch"}


def main(args: Namespace) -> int:
    explorer_command = ALIAS_TO_COMMAND.get(
        args.explorer_command, args.explorer_command
    )
    if explorer_command == "list":
        list_supported_explorers(args.by_id, json=args.json)
    elif explorer_command == "fetch":
        boa_get_abi_from_explorer(
            args.address,
            name=args.name,
            explorer_uri=args.explorer_uri,
            explorer_type=args.explorer_type,
            api_key=args.api_key,
            save_abi_path=args.save_abi_path,
            save=args.save,
            ignore_config=args.ignore_config,
            network_name_or_id=args.network,
        )
    else:
        logger.warning(f"Unknown explorer command: {args.explorer_command}")
    return 0


def boa_get_abi_from_explorer(
    address: str,
    name: str | None = None,
    explorer_uri: str | None = None,
    explorer_type: str | None = None,
    api_key: str | None = None,
    save_abi_path: str | None = None,
    save: bool = False,
    ignore_config: bool = False,
    network_name_or_id: str = "",
    quiet: bool = False,  # This is for when this function is used as a library
) -> list:
    if quiet:
        set_log_level(quiet=True)

    network: Network | None = None
    # 1. If not ignore_config, grab stuff from the config
    if not ignore_config:
        config = get_or_initialize_config()
        if network_name_or_id is None:
            network_name_or_id = config.default_network
        if network_name_or_id:
            network = config.networks.get_network(network_name_or_id)
            network = cast(Network, network)
            if network.chain_id:
                network_name_or_id = str(network.chain_id)
        if network is not None:
            if not explorer_uri:
                explorer_uri = network.explorer_uri
            if not explorer_type:
                explorer_type = network.explorer_type
            if not api_key:
                api_key = network.explorer_api_key
            if not save_abi_path:
                save_abi_path = network.save_abi_path
        if not save_abi_path:
            save_abi_path = config.project.get("save_abi_path", None)

    # 2. If you still don't have a explorer_uri, check the default networks
    if not explorer_uri:
        if str(network_name_or_id).isdigit():
            chain_id = int(network_name_or_id)
            explorer_uri = DEFAULT_NETWORKS_BY_CHAIN_ID.get(chain_id, {}).get(
                "explorer_uri"
            )
        else:
            explorer_uri = DEFAULT_NETWORKS_BY_NAME.get(network_name_or_id, {}).get(
                "explorer_uri"
            )

    # 3. Only for api, finally, check ENV variable
    if not api_key:
        api_key = os.getenv(DEFAULT_API_KEY_ENV_VAR)

    if not api_key:
        raise ValueError(
            f"No API key provided. Please provide one in the command line with --api-key or set the environment variable:\n{DEFAULT_API_KEY_ENV_VAR}"
        )
    if (save and save_abi_path and not name) or (save and not save_abi_path):
        raise ValueError(
            "If you wish to save the ABI, you must also provide both a --name and a --save-abi-path."
        )

    abi: list = []
    if explorer_type != "etherscan":
        logger.warning(
            "As of today, fetching only works with Etherscan style explorers."
        )
    with boa.set_etherscan(explorer_uri, api_key=api_key):
        explorer = boa.explorer.get_etherscan()
        abi = explorer.fetch_abi(address)
        if len(abi) == 0:
            logger.warning(f"No ABI found for address: {address}")
            return abi

    if save_abi_path and save:
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
