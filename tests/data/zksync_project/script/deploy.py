from src import Difficulty

from moccasin.boa_tools import ZksyncContract

# from boa.contracts.vyper.vyper_contract import VyperContract


def deploy() -> ZksyncContract:
    difficulty: ZksyncContract = Difficulty.deploy()
    print("Difficulty: ", difficulty.get_difficulty())
    return difficulty


def moccasin_main() -> ZksyncContract:
    return deploy()
