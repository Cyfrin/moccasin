from typing import Union
from moccasin.boa_tools import VyperContract
from moccasin.config import get_config
from contracts import BuyMeACoffee


# Test to make sure the same address is returned when calling
# manifest twice
def manifest_many_times():
    active_network = get_config().get_active_network()
    price_feed_one: VyperContract = active_network.get_or_deploy_contract("price_feed")
    print(price_feed_one.address)
    price_feed_two: VyperContract = active_network.manifest_contract("price_feed")
    print(price_feed_two.address)
    price_feed_three: VyperContract = active_network.get_or_deploy_contract(
        "price_feed"
    )
    print(price_feed_three.address)
    price_feed_different: VyperContract = active_network.get_or_deploy_contract(
        "price_feed", force_deploy=True
    )
    print(price_feed_different.address)


def moccasin_main():
    return manifest_many_times()
