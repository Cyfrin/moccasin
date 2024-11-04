import os
from pathlib import Path

from moccasin.commands.inspect import inspect_contract
from tests.conftest import COMPLEX_PROJECT_PATH


def test_inspect_counter(complex_project_config):
    expected_dir = {
        "set_number(uint256)": "0xd6d1ee14 (3604082196)",
        "increment()": "0xd09de08a (3500007562)",
        "number()": "0x8381f58a (2206332298)",
        "other_number()": "0x81593bc0 (2170108864)",
    }
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(COMPLEX_PROJECT_PATH))
        result = inspect_contract("Counter", "function_signatures", print_out=False)
    finally:
        os.chdir(current_dir)
    assert result == expected_dir
