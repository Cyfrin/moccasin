from src import Counter
from gaboon.boa_tools import ZksyncContract

# from boa.contracts.vyper.vyper_contract import VyperContract

def deploy() -> ZksyncContract:
    counter: ZksyncContract = Counter.deploy()
    print("Starting count: ", counter.number())
    counter.increment()
    print("Ending count: ", counter.number())
    return counter


def main() -> ZksyncContract:
    return deploy()
