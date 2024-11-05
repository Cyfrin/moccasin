import pytest
from script.deploy import deploy

@pytest.fixture
def counter_contract():
    return deploy()