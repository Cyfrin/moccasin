from argparse import Namespace
from enum import Enum

from boa.deployments import Deployment

from moccasin.config import Config, get_config, initialize_global_config
from moccasin.logging import logger

NUM_DASH = 60


class PrintVerbosity(Enum):
    CONTRACT_ADDRESS = 0  # Only the contract address
    CONTRACT_ADDRESS_AND_NAME = 1  # Contract address and contract name
    ADDRESS_NAME_DEPLOYER = 2  # Address, name, and deployer address
    FULL_DETAILS = 3  # All available details
    RAW = 4  # Raw deployment object


def main(args: Namespace) -> int:
    initialize_global_config()
    print_deployments_from_cli(
        args.contract_name,
        args.format_level,
        args.db_path,
        args.checked,
        args.limit,
        args.network,
        args.url,
        args.fork,
    )
    return 0


def print_deployments_from_cli(
    contract_name: str | None = None,
    format_level: int = PrintVerbosity.CONTRACT_ADDRESS_AND_NAME.value,
    db_path: str | None = None,
    checked: bool = False,
    limit: int | None = None,
    network: str = None,
    url: str = None,
    fork: bool = None,
    config: Config | None = None,
) -> list[Deployment]:
    if config is None:
        config = get_config()

    if contract_name is not None:
        if contract_name.strip().lower() == "all":
            contract_name = None

    if network is None:
        network = config.default_network

    # Don't activate boa
    config.set_active_network(
        network, url=url, fork=fork, db_path=db_path, activate_boa=False
    )
    active_network = config.get_active_network()

    if not hasattr(active_network, "chain_id"):
        logger.warning(
            "No chain_id found in active network, attempting to connect to the network to retrieve the Chain Id"
        )
        active_network.create_and_set_or_set_boa_env()

    if not active_network.save_to_db or not active_network.db_path:
        logger.error(
            f"Cannot get deployments without a database path on network {active_network.name}.\nPlease specify one or change networks."
        )
        return []

    deployments_list = []
    if not isinstance(limit, int) and not isinstance(limit, type(None)):
        raise ValueError(f"Limit must be an integer or None, not {type(limit)}.")
    if checked:
        deployments_list = active_network.get_deployments_checked(
            contract_name=contract_name, limit=limit, chain_id=active_network.chain_id
        )
    else:
        deployments_list = active_network.get_deployments_unchecked(
            contract_name=contract_name, limit=limit, chain_id=active_network.chain_id
        )

    int_format_level = int(format_level)
    if int_format_level > len(PrintVerbosity):
        int_format_level = PrintVerbosity.RAW.value

    print_deployments(deployments_list, PrintVerbosity(int_format_level))
    return deployments_list


def print_deployments(deployments_list: list[Deployment], format_level: PrintVerbosity):
    if len(deployments_list) > 0:
        print("-" * NUM_DASH)
    for deployment in deployments_list:
        if format_level == PrintVerbosity.CONTRACT_ADDRESS:
            print(f"Contract Address: {deployment.contract_address}")
            continue

        elif format_level == PrintVerbosity.CONTRACT_ADDRESS_AND_NAME:
            print(f"Contract Address: {deployment.contract_address}")
            print(f"Contract Name: {deployment.contract_name}")
            print(f"Deployer: {deployment.deployer}")
            print("-" * NUM_DASH)
            continue

        elif format_level == PrintVerbosity.ADDRESS_NAME_DEPLOYER:
            print(f"Contract Address: {deployment.contract_address}")
            print(f"Contract Name: {deployment.contract_name}")
            print(f"Deployer: {deployment.deployer}")
            print(f"RPC: {deployment.rpc}")
            print(f"Transaction Hash: {deployment.tx_hash}")
            print("Source Code:")
            for file_name, content in deployment.source_code["sources"].items():
                print(f"  File: {file_name}")
                print("  Content:")
                print(content["content"][:200] + "...")  # Print first 200 characters
            print("-" * NUM_DASH)
            continue

        elif format_level == PrintVerbosity.FULL_DETAILS:
            print(f"Contract Address: {deployment.contract_address}")
            print(f"Contract Name: {deployment.contract_name}")
            print(f"Deployer: {deployment.deployer}")
            print(f"RPC: {deployment.rpc}")
            print(f"Transaction Hash: {deployment.tx_hash}")
            print(f"Broadcast Timestamp: {deployment.broadcast_ts}")
            print("Transaction Dict:")
            for key, value in deployment.tx_dict.items():
                print(f"  {key}: {value}")
            print("Receipt Dict:")
            for key, value in deployment.receipt_dict.items():
                print(f"  {key}: {value}")
            print("Source Code:")
            for file_name, content in deployment.source_code["sources"].items():
                print(f"  File: {file_name}")
                print("  Content:")
                print(content["content"])
            print("ABI:")
            for item in deployment.abi:
                print(f"  {item}")
            print(f"Session ID: {deployment.session_id}")
            print(f"Deployment ID: {deployment.deployment_id}")
            print("-" * NUM_DASH)
            continue

        elif format_level == PrintVerbosity.RAW:
            print(deployment)
            print("-" * NUM_DASH)
            continue

    print(f"Total deployments: {len(deployments_list)}")
    return deployments_list
