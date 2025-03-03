import json
import os
import subprocess
from pathlib import Path

import pytest

from moccasin.commands.compile import compile_
from moccasin.commands.run import run_script


def test_compile_zksync_pyevm(
    zksync_cleanup_out_folder, zk_temp_path, zksync_out_folder, mox_path
):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(zk_temp_path))
        result = subprocess.run(
            [mox_path, "build", "Difficulty.vy", "--network", "pyevm"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Done compiling Difficulty" in result.stderr
    assert result.returncode == 0
    # read the Difficulty.json in zksync_out_folder
    with open(
        zk_temp_path.joinpath(zksync_out_folder).joinpath("Difficulty.json"), "r"
    ) as f:
        data = json.load(f)
        assert data["vm"] == "evm"


def test_compile_zksync_one(
    zksync_cleanup_out_folder, zk_temp_path, zksync_out_folder, zksync_test_env
):
    compile_(
        zk_temp_path.joinpath("src/Difficulty.vy"),
        zk_temp_path.joinpath(zksync_out_folder),
        is_zksync=True,
        write_data=True,
    )
    with open(
        zk_temp_path.joinpath(zksync_out_folder).joinpath("Difficulty.json"), "r"
    ) as f:
        data = json.load(f)
        assert data["vm"] == "eravm"


def test_compile_zksync_bad(
    zksync_cleanup_out_folder, zk_temp_path, zksync_out_folder, zksync_test_env
):
    with pytest.raises(AssertionError) as excinfo:
        compile_(
            zk_temp_path.joinpath("src/SelfDestruct.vy"),
            zk_temp_path.joinpath(zksync_out_folder),
            is_zksync=True,
            write_data=True,
        )
    error_message = str(excinfo.value)
    assert "subprocess compiling" in error_message
    assert "failed with exit code Some(1)" in error_message
    assert "The `SELFDESTRUCT` instruction is not supported" in error_message


def test_run_zksync_good(zksync_cleanup_out_folder, zk_temp_path, zksync_test_env):
    difficulty_contract = run_script(zk_temp_path.joinpath("script/deploy.py"))
    difficulty = difficulty_contract.get_difficulty()
    assert difficulty == 2500000000000000
