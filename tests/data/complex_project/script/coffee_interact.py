from boa.contracts.abi.abi_contract import ABIContract
from eth_utils import to_wei

from moccasin.config import get_active_network


def fund_coffee() -> ABIContract:
    active_network = get_active_network()
    # coffee = active_network.get_latest_contract_checked("BuyMeACoffee")
    coffee = active_network.manifest_named("BuyMeACoffee")

    account = active_network.get_default_account()
    active_network.set_boa_eoa(account)
    value = to_wei(1, "ether")
    coffee.fund(value=value)
    print("Funded BuyMeACoffee contract with 1 ether")
    return coffee


def moccasin_main():
    fund_coffee()
