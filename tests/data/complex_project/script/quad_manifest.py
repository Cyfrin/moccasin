from moccasin.boa_tools import VyperContract
from moccasin.config import get_config
from script.mock_deployer.deploy_feed import deploy_mock


# Test to make sure the same address is returned when calling
# manifest twice
def manifest_many_times():
    price_feed_zero = deploy_mock()
    print(price_feed_zero.address)

    active_network = get_config().get_active_network()
    price_feed_one: VyperContract = active_network.get_or_deploy_named_contract(
        "price_feed"
    )
    print(price_feed_one.address)
    price_feed_two: VyperContract = active_network.manifest_named("price_feed")
    print(price_feed_two.address)
    price_feed_three: VyperContract = active_network.get_or_deploy_named_contract(
        "price_feed"
    )
    print(price_feed_three.address)

    price_feed_four: VyperContract = active_network.get_or_deploy_named_contract(
        "price_feed", force_deploy=True
    )
    print(price_feed_four.address)

    price_feed_five = deploy_mock()
    print(price_feed_five.address)

    # This should be new!
    price_feed_six = active_network.get_or_deploy_named_contract("other_price_feed")
    print(price_feed_six.address)

    price_feed_seven = active_network.get_or_deploy_named_contract("price_feed")
    print(price_feed_seven.address)

    price_feed_eight = active_network.get_or_deploy_named_contract("other_price_feed")
    print(price_feed_eight.address)


def moccasin_main():
    return manifest_many_times()
