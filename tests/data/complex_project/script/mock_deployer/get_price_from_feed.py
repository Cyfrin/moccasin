from moccasin.config import get_config


def get_price_from_feed():
    config = get_config()
    active_network = config.get_active_network()
    price_feed = active_network.manifest_contract("price_feed")


def moccasin_main():
    get_price_from_feed()
