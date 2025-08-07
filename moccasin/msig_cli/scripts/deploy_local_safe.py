import os
from typing import Optional

from eth_typing import ChecksumAddress
from regex import E
from requests.exceptions import ConnectionError

from moccasin.moccasin_account import MoccasinAccount
from safe_eth.eth import EthereumClient
from safe_eth.safe.multi_send import MultiSend
from safe_eth.safe.safe import SafeV141

from moccasin.constants.vars import DEFAULT_ANVIL_PRIVATE_KEY, DEFAULT_ANVIL_URL


def deploy_local_safe_anvil() -> tuple[
    Optional[ChecksumAddress], Optional[ChecksumAddress]
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
    ethereum_client = EthereumClient(DEFAULT_ANVIL_URL)

    # Deploy a Safe instance form class method
    safe_eth_tx = SafeV141.deploy_contract(
        ethereum_client=ethereum_client, deployer_account=deployer
    )

    # Deploy a MultiSend contract and set the address in the environment variable
    multisend_eth_tx = MultiSend.deploy_contract(
        ethereum_client=ethereum_client, deployer_account=deployer
    )
    os.environ["TEST_MULTISEND_ADDRESS"] = multisend_eth_tx.contract_address

    return safe_eth_tx.contract_address, multisend_eth_tx.contract_address


if __name__ == "__main__":
    try:
        eth_safe_address, eth_multisend_address = deploy_local_safe_anvil()
        if eth_safe_address is None:
            raise Exception("Failed to deploy Safe contract.")
        else:
            print(f"Safe deployed successfully: {eth_safe_address}")
        if eth_multisend_address is None:
            raise Exception("Failed to deploy MultiSend contract.")
        else:
            print(f"MultiSend deployed successfully: {eth_multisend_address}")
    except ConnectionError:
        print("Error: Could not connect to Anvil at localhost:8545. Is Anvil running?")
    except Exception as e:
        print(f"Error deploying Safe: {e}")
