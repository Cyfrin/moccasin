import inspect
from types import ModuleType
from typing import Callable, Literal, cast

from boa.contracts.abi.abi_contract import ABIContract
from boa.contracts.vyper.vyper_contract import VyperContract
from pytest import fixture

from moccasin.config import get_config

ScopeType = Literal["function", "class", "module", "package", "session"]


def request_fixtures(
    fixture_requests: list[str | tuple[str, str]], scope: str = "module"
):
    # Dear Charles, don't kill me. Idk how this works.
    current_frame = inspect.currentframe()
    if current_frame is None or current_frame.f_back is None:
        raise RuntimeError("Cannot determine caller module")
    caller_frame = current_frame.f_back

    caller_module = inspect.getmodule(caller_frame)
    if caller_module is None:
        raise RuntimeError("Cannot determine caller module")
    module: ModuleType = caller_module
    for fixture_request in fixture_requests:
        if isinstance(fixture_request, tuple):
            named_contract_name, fixture_name = fixture_request
        else:
            named_contract_name = fixture_request
            fixture_name = named_contract_name
        request_fixture(module, named_contract_name, fixture_name, scope)


def request_fixture(
    module: ModuleType,
    named_contract_name: str,
    fixture_name: str,
    scope: str = "module",
):
    active_network = get_config().get_active_network()
    named_contract = active_network.get_named_contract(named_contract_name)
    if named_contract is None:
        raise ValueError(
            f"No contract found for contract '{named_contract_name}' on network {active_network.name}"
        )
    if named_contract.deployer_script is None:
        raise ValueError(
            f"No deploy function found for '{named_contract_name}' on network {active_network.name}"
        )

    def deploy_func() -> VyperContract | ABIContract:
        return active_network.get_or_deploy_contract(named_contract_name)

    # Create the fixture function
    fixture_function = make_fixture(deploy_func, fixture_name, cast(ScopeType, scope))

    # Add the fixture to the module's namespace
    setattr(module, fixture_name, fixture_function)


def make_fixture(
    deploy_func: Callable[[], VyperContract | ABIContract],
    fixture_name: str,
    scope: Literal["function", "class", "module", "package", "session"],
) -> Callable[[], VyperContract | ABIContract]:
    @fixture(scope=scope, name=fixture_name)
    def fixture_func(deploy_func=deploy_func):
        return deploy_func()

    return cast(Callable[[], VyperContract | ABIContract], fixture_func)
