from src.mocks import mock_token

from moccasin.boa_tools import VyperContract
from moccasin.config import get_active_network


def deploy_collateral() -> VyperContract:
    print("Deploying token...")
    mock_token_contract = mock_token.deploy()

    active_network = get_active_network()
    if active_network.has_explorer():
        print("Verifying contract on explorer...")
        result = active_network.moccasin_verify(mock_token_contract)
        result.wait_for_verification()

    print(f"Deployed Mock Token contract at {mock_token_contract.address}")
    return mock_token_contract


def moccasin_main():
    return deploy_collateral()
