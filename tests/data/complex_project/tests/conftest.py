import pytest
from script.deploy import deploy
from script.deploy_coffee import deploy as deploy_coffee
from script.mock_deployer.deploy_feed import deploy_mock


@pytest.fixture
def price_feed():
    return deploy_mock()


@pytest.fixture
def eth_usd():
    return deploy_mock()


@pytest.fixture
def counter_contract():
    return deploy()


@pytest.fixture
def coffee():
    return deploy_coffee()
