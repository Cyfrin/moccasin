from contracts.mocks import MockV3Aggregator

from moccasin.boa_tools import VyperContract

DECIMALS = 18
INITIAL_ANSWER = int(2000e18)


def deploy_mock() -> VyperContract:
    aggregator = MockV3Aggregator.deploy(DECIMALS, INITIAL_ANSWER)
    return aggregator


def moccasin_main() -> VyperContract:
    return deploy_mock()
