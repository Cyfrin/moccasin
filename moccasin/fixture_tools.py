import inspect
from types import ModuleType
from typing import Callable, Literal, cast

from boa.contracts.abi.abi_contract import ABIContract
from boa.contracts.vyper.vyper_contract import VyperContract
import pytest

from moccasin.config import get_config


# REVIEW: fixture_requests should probably always be a list of strings
def request_fixtures(
    fixture_requests: list[str | tuple[str, str]], scope: str = "module"
):
    for fixture_request in fixture_requests:
        if isinstance(fixture_request, tuple):
            contract_name, fixture_name = fixture_request
        else:
            # sanity check
            assert isinstance(fixture_request, str)
            contract_name = fixture_request
            fixture_name = None

        request_fixture(contract_name, fixture_name, scope)

def _find_calling_module() -> ModuleType:
    current_frame = inspect.currentframe()
    if current_frame is None:
        raise RuntimeError("Cannot determine caller module")

    this_module = inspect.getmodule(current_frame)

    while True:
        module = inspect.getmodule(current_frame)
        if module is None:
            raise RuntimeError("Cannot determine caller module")

        # found the first caller frame that is not this module
        if module is not this_module:
            return module

        # go up a frame
        current_frame = current_frame.f_back
        if current_frame is None:
            raise RuntimeError("Cannot determine caller module")


def request_fixture(
    contract_name: str,
    fixture_name: str = None,
    scope: str = "module",
):
    fixture_name = fixture_name or contract_name

    module = _find_calling_module()

    active_network = get_config().get_active_network()
    named_contract = active_network.get_named_contract(named_contract_name)
    if named_contract is None:
        raise ValueError(
            f"No contract found for contract '{contract_name}' on network {active_network.name}"
        )
    if named_contract.deployer_script is None:
        raise ValueError(
            f"No deploy function found for '{contract_name}' on network {active_network.name}"
        )

    @pytest.fixture(scope=scope, name=fixture_name)
    def _fixture():
        return active_network.get_or_deploy_contract(contract_name)

    # add the fixture to the module's namespace
    # REVIEW: i don't think is actually necessary?
    setattr(module, fixture_name, _fixture)
