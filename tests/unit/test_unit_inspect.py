import os
from argparse import Namespace
from pathlib import Path

from moccasin.commands.inspect import inspect_contract, main
from tests.conftest import COMPLEX_PROJECT_PATH


def test_inspect_counter(complex_project_config):
    expected_dir = {
        "set_number(uint256)": "0xd6d1ee14 (3604082196)",
        "increment()": "0xd09de08a (3500007562)",
    }
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(COMPLEX_PROJECT_PATH))
        result = inspect_contract("Counter", "function_signatures", print_out=False)
    finally:
        os.chdir(current_dir)
    assert result == expected_dir


def test_inspect_cli_initiates_config(capsys):
    expected_dir = {
        "set_number(uint256)": "0xd6d1ee14 (3604082196)",
        "increment()": "0xd09de08a (3500007562)",
    }
    args = Namespace(
        contract="Counter", inspect_type="function_signatures", print_out=True
    )
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(COMPLEX_PROJECT_PATH))
        main(args)
    finally:
        os.chdir(current_dir)
    output = capsys.readouterr()
    assert expected_dir["set_number(uint256)"] in output.out
    assert expected_dir["increment()"] in output.out
