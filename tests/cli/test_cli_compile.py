import os
import subprocess
from pathlib import Path

from tests.constants import LIB_GH_PATH, LIB_PIP_PATH

EXPECTED_HELP_TEXT = "Vyper compiler"


def test_compile_help(mox_path):
    result = subprocess.run(
        [mox_path, "compile", "-h"], check=True, capture_output=True, text=True
    )
    assert EXPECTED_HELP_TEXT in result.stdout, (
        "Help output does not contain expected text"
    )
    assert result.returncode == 0


def test_build_help(mox_path):
    result = subprocess.run(
        [mox_path, "build", "-h"], check=True, capture_output=True, text=True
    )
    assert EXPECTED_HELP_TEXT in result.stdout, (
        "Help output does not contain expected text"
    )
    assert result.returncode == 0


def test_compile_alias_build_project(
    complex_temp_path,
    complex_cleanup_out_folder,
    complex_cleanup_dependencies_folder,
    mox_path,
):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        result = subprocess.run(
            [mox_path, "build"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    # Count the number of contracts in the contracts/ directory
    # @dev avoid interfaces folder
    contract_dir = complex_temp_path.joinpath("contracts")
    contract_count = sum(
        [
            len(files)
            for root, _, files in os.walk(contract_dir)
            if "interfaces" not in root
        ]
    )

    assert complex_temp_path.joinpath().exists()

    assert "Running compile command" in result.stderr
    assert f"Compiling {contract_count} contracts to build/..." in result.stderr
    assert "Done compiling project!" in result.stderr
    assert result.returncode == 0


def test_compile_one(complex_temp_path, complex_cleanup_out_folder, mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        result = subprocess.run(
            [mox_path, "build", "BuyMeACoffee.vy", "--no-install"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)

    assert not complex_temp_path.joinpath(LIB_GH_PATH).exists()
    assert not complex_temp_path.joinpath(LIB_PIP_PATH).exists()
    assert "Done compiling BuyMeACoffee" in result.stderr
    assert result.returncode == 0
