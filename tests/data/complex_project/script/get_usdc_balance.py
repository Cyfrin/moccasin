from gaboon import config
from boa.contracts.vyper.vyper_contract import VyperDeployer
from src import MyToken


def get_decimals():
    active_network = config.get_config().get_active_network()
    usdc: VyperDeployer = MyToken.at(active_network.extra_data["usdc"])
    decimals = usdc.decimals()
    print(decimals)


def main():
    get_decimals()
