import pytest
from script.deploy import deploy
from moccasin.fixture_tools import request_fixtures

request_fixtures(["price_feed", ("price_feed", "eth_usd")], scope="session")


@pytest.fixture
def counter_contract():
    return deploy()
