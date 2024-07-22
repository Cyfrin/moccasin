from boa.contracts.vyper.vyper_contract import VyperDeployer

from gaboon.cli.compile import compile
from tests.base_test import COUNTER_PROJECT_FILE_PATH, COUNTER_PROJECT_PATH


def test_compile():
    result: VyperDeployer = compile(COUNTER_PROJECT_FILE_PATH, write_data=False)
    isinstance(result, VyperDeployer)


def test_compile_write_data(cleanup_out_folder):
    compile(COUNTER_PROJECT_FILE_PATH, write_data=True)
    assert COUNTER_PROJECT_PATH.joinpath("out/Counter.json").exists()
