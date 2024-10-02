from src import Counter
from moccasin.boa_tools import VyperContract
# from boa.contracts.vyper.vyper_contract import VyperContract

def deploy() -> VyperContract:
    counter: VyperContract = Counter.deploy()
    print("Starting count: ", counter.number())
    counter.increment()
    print("Ending count: ", counter.number())
    return counter

def moccasin_main() -> VyperContract:
    return deploy()
