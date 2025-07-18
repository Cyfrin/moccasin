from src.mocks import MockV3Aggregator

DECIMALS = 8
INITIAL_VALUE = 200_000_000_000  # $2,000


def deploy_price_feed():
    return MockV3Aggregator.deploy(DECIMALS, INITIAL_VALUE)


def moccasin_main():
    return deploy_price_feed()
