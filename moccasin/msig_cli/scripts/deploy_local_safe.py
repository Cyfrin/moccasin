import os
import traceback
from typing import Optional

from eth_typing import URI, ChecksumAddress
from requests.exceptions import ConnectionError
from safe_eth.eth import EthereumClient
from safe_eth.eth.contracts import get_proxy_factory_contract, get_safe_V1_4_1_contract
from safe_eth.eth.utils import get_empty_tx_params
from safe_eth.safe.multi_send import MultiSend
from safe_eth.safe.proxy_factory import ProxyFactory
from safe_eth.safe.safe import SafeV141
from safe_eth.safe.compatibility_fallback_handler import (
    CompatibilityFallbackHandlerV141,
)

from moccasin.constants.vars import DEFAULT_ANVIL_PRIVATE_KEY, DEFAULT_ANVIL_URL
from moccasin.moccasin_account import MoccasinAccount

DEFAULT_ANVIL_OWNERS = [
    "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
    "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
    "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
    "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc",
    "0x976EA74026E726554dB657fA54763abd0C3a0aa9",
    "0x14dC79964da2C08b23698B3D3cc7Ca32193d9955",
    "0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f",
    "0xa0Ee7A142d267C1f36714E4a8F75612F20a79720",
]

FUND_SAFE_PROXY_AMOUNT = int(10 * 10**18)  # 10 ETH in wei

# @TODO typecheck mypy


def deploy_local_safe_anvil() -> tuple[
    Optional[ChecksumAddress], Optional[ChecksumAddress], Optional[ChecksumAddress]
]:
    """Deploy a local Safe instance on Anvil and set up MultiSend address.

    This function sets up the environment variables for the Safe and deploys a MultiSend contract.

    @dev You need to have Anvil running on port 8545.
    """
    # Setup env variables for Safe
    os.environ["ETHEREUM_NODE_URL"] = DEFAULT_ANVIL_URL
    os.environ["ETHEREUM_TEST_PRIVATE_KEY"] = DEFAULT_ANVIL_PRIVATE_KEY

    # Deployer account and EthereumClient for Safe
    deployer = MoccasinAccount(private_key=DEFAULT_ANVIL_PRIVATE_KEY)
    ethereum_client = EthereumClient(URI(DEFAULT_ANVIL_URL))

    # Deploy Safe master copy
    safe_master_tx = SafeV141.deploy_contract(
        ethereum_client=ethereum_client, deployer_account=deployer
    )
    safe_master_address = safe_master_tx.contract_address
    if safe_master_address is None:
        raise Exception("Failed to deploy Safe master copy.")

    # Deploy ProxyFactory
    proxy_factory_contract = get_proxy_factory_contract(ethereum_client.w3)
    tx_hash = proxy_factory_contract.constructor().transact({"from": deployer.address})
    tx_receipt = ethereum_client.w3.eth.wait_for_transaction_receipt(tx_hash)
    assert tx_receipt["status"] == 1, "Problem deploying ProxyFactory"
    proxy_factory_address = tx_receipt["contractAddress"]
    proxy_factory = ProxyFactory(proxy_factory_address, ethereum_client)  # type: ignore

    # Deploy CompatibilityFallbackHandler contract (for simulation)
    fallback_handler_tx = CompatibilityFallbackHandlerV141.deploy_contract(
        ethereum_client=ethereum_client, deployer_account=deployer
    )
    fallback_handler_address = fallback_handler_tx.contract_address
    if fallback_handler_address is None:
        raise Exception("Failed to deploy CompatibilityFallbackHandler.")

    # Owners and threshold for local testing
    owners = [deployer.address, *DEFAULT_ANVIL_OWNERS]
    threshold = 2
    fallback_handler = fallback_handler_address
    to = "0x0000000000000000000000000000000000000000"
    data = b""
    payment_token = "0x0000000000000000000000000000000000000000"
    payment = 0
    payment_receiver = "0x0000000000000000000000000000000000000000"
    initializer_contract = get_safe_V1_4_1_contract(
        ethereum_client.w3, safe_master_address
    )
    initializer_data = initializer_contract.functions.setup(
        owners,
        threshold,
        to,
        data,
        fallback_handler,
        payment_token,
        payment,
        payment_receiver,
    ).build_transaction(get_empty_tx_params())["data"]
    # Ensure initializer is bytes
    initializer = b""
    if isinstance(initializer_data, str):
        initializer = bytes.fromhex(initializer_data.lstrip("0x"))
    elif isinstance(initializer_data, bytes):
        initializer = initializer_data

    # Deploy Safe proxy with initializer
    safe_proxy_tx = proxy_factory.deploy_proxy_contract_with_nonce(
        deployer, safe_master_address, initializer=initializer
    )
    safe_proxy_address = safe_proxy_tx.contract_address

    # Fund the Safe proxy address with ETH
    fund_amount = FUND_SAFE_PROXY_AMOUNT
    tx_hash = ethereum_client.w3.eth.send_transaction(
        {"from": deployer.address, "to": safe_proxy_address, "value": fund_amount}
    )
    ethereum_client.w3.eth.wait_for_transaction_receipt(tx_hash)

    # Deploy a MultiSend contract and set the address in the environment variable
    multisend_eth_tx = MultiSend.deploy_contract(
        ethereum_client=ethereum_client, deployer_account=deployer
    )
    os.environ["TEST_MULTISEND_ADDRESS"] = str(multisend_eth_tx.contract_address)

    return (
        safe_proxy_address,
        multisend_eth_tx.contract_address,
        fallback_handler_address,
    )


if __name__ == "__main__":
    try:
        eth_safe_address, eth_multisend_address, eth_fallback_handler_address = (
            deploy_local_safe_anvil()
        )
        if eth_safe_address is None:
            raise Exception("Failed to deploy Safe contract.")
        else:
            print(f"Safe deployed successfully: {eth_safe_address}")
        if eth_multisend_address is None:
            raise Exception("Failed to deploy MultiSend contract.")
        else:
            print(f"MultiSend deployed successfully: {eth_multisend_address}")
        if eth_fallback_handler_address is None:
            raise Exception("Failed to deploy CompatibilityFallbackHandler contract.")
        else:
            print(
                f"CompatibilityFallbackHandler deployed successfully: {eth_fallback_handler_address}"
            )
    except ConnectionError:
        print("Error: Could not connect to Anvil at localhost:8545. Is Anvil running?")
    except Exception as e:
        print(f"Error deploying Safe: {e}")
        traceback.print_exc()
