from src import Counter
from boa.contracts.vyper.vyper_contract import VyperContract

# from boa import project
# project.accounts
# project.get_active_account()
# project.get_active_network()
# project.networks
# boa.set_env(project.networks[0].rpc)

# from gaboon import magic_config
# import gaboon


def deploy() -> VyperContract:
    # gaboon.get_running_config()  # could return a config object, which is essentially a dict with plumbing
    counter: VyperContract = Counter.deploy()
    print("Starting count: ", counter.number())
    counter.increment()
    print("Ending count: ", counter.number())
    return counter


def main() -> VyperContract:
    return deploy()
