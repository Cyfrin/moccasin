import pytest
from script.deploy_coffee import deploy as deploy_coffee
from script.mock_deployer.deploy_feed import deploy_mock

from moccasin.config import get_config


@pytest.fixture
def active_network():
    return get_config().get_active_network()


@pytest.fixture
def price_feed(active_network):
    return active_network.manifest_named("price_feed")


@pytest.fixture
def eth_usd():
    return deploy_mock()


@pytest.fixture
def counter_contract():
    active_network = get_config().get_active_network()
    return active_network.manifest_named("counter")


@pytest.fixture
def coffee():
    return deploy_coffee()
