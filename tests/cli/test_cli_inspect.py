import os
import subprocess
from pathlib import Path

from moccasin.commands.inspect import inspect_contract


def test_inspect_layout_imports(mox_path, installation_project_config, installation_temp_path):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(installation_temp_path))
        result = subprocess.run(
            [mox_path, "install"], check=True, capture_output=True, text=True
        )
        result = inspect_contract("MyToken", "storage_layout", print_out=False)
    finally:
        os.chdir(current_dir)
    layout = result["storage_layout"]
    # Spot check
    assert layout["ow"]["owner"] == {'type': 'address', 'n_slots': 1, 'slot': 0}
    assert layout["erc20"]["balanceOf"] == {'type': 'HashMap[address, uint256]', 'n_slots': 1, 'slot': 1}