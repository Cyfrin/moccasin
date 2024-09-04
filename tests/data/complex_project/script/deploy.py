from src import Counter
from gaboon.boa_tools import VyperContract


def deploy() -> VyperContract:
    # gaboon.get_running_config()  # could return a config object, which is essentially a dict with plumbing
    counter: VyperContract = Counter.deploy()
    print("Starting count: ", counter.number())
    counter.increment()
    print("Ending count: ", counter.number())
    return counter


def main() -> VyperContract:
    return deploy()
