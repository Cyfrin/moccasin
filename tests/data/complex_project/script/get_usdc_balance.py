from moccasin import config
from boa.contracts.vyper.vyper_contract import VyperContract


def get_decimals():
    active_network = config.get_config().get_active_network()
    # usdc: VyperDeployer = MyToken.at(active_network.extra_data["usdc"])
    usdc: VyperContract = active_network.manifest_contract("usdc")
    decimals = usdc.decimals()
    print(decimals)


def moccasin_main():
    get_decimals()
