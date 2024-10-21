from boa.contracts.vyper.vyper_contract import VyperContract

from moccasin import config


def get_decimals():
    active_network = config.get_config().get_active_network()
    # usdc: VyperDeployer = MyToken.at(active_network.extra_data["usdc"])
    usdc: VyperContract = active_network.manifest_named("usdc")
    decimals = usdc.decimals()
    print(decimals)


def moccasin_main():
    get_decimals()
