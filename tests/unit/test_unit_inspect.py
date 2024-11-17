import os
from pathlib import Path

from moccasin.commands.inspect import inspect_contract


def test_inspect_counter(complex_project_config, complex_temp_path):
    expected_dir = {
        "set_number(uint256)": "0xd6d1ee14 (3604082196)",
        "increment()": "0xd09de08a (3500007562)",
        "number()": "0x8381f58a (2206332298)",
        "other_number()": "0x81593bc0 (2170108864)",
    }
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        result = inspect_contract("Counter", "function_signatures", print_out=False)
    finally:
        os.chdir(current_dir)
    assert result == expected_dir

def test_inspect_layout_imports(installation_project_config, installation_temp_path):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(installation_temp_path))
        result = inspect_contract("MyToken", "storage_layout", print_out=False)
    finally:
        os.chdir(current_dir)
    layout = result["storage_layout"]
    # Spot check
    assert layout["ow"]["owner"] == {'type': 'address', 'n_slots': 1, 'slot': 0}
    assert layout["erc20"]["balanceOf"] == {'type': 'HashMap[address, uint256]', 'n_slots': 1, 'slot': 1}