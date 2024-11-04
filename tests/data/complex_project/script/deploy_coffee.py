from contracts import BuyMeACoffee

from moccasin.boa_tools import VyperContract
from moccasin.config import get_config


def deploy() -> VyperContract:
    active_network = get_config().get_active_network()
    price_feed: VyperContract = active_network.get_or_deploy_named_contract(
        "price_feed"
    )
    buy_me_a_coffe: VyperContract = BuyMeACoffee.deploy(price_feed.address)
    print(f"Deployed BuyMeACoffee to {buy_me_a_coffe.address}")
    return buy_me_a_coffe


def moccasin_main() -> VyperContract:
    return deploy()
