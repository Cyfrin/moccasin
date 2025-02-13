import os
import subprocess
from pathlib import Path

from moccasin.config import Config
from tests.constants import (
    COMPLEX_UPDATE_PACKAGES_TOML,
    LIB_GH_PATH,
    LIB_PIP_PATH,
    NEW_VERSION,
    PATRICK_PACKAGE_NAME,
    PIP_PACKAGE_NAME,
)

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
    complex_temp_path, complex_cleanup_dependencies_folder, mox_path
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

    assert complex_temp_path.joinpath(LIB_PIP_PATH).exists()

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


def test_compile_and_update(complex_temp_path, complex_cleanup_out_folder, mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        result = subprocess.run(
            [mox_path, "build", "BuyMeACoffee.vy"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)

    assert not complex_temp_path.joinpath(LIB_GH_PATH).exists()
    assert complex_temp_path.joinpath(LIB_PIP_PATH).exists()
    assert "Done compiling BuyMeACoffee" in result.stderr
    assert result.returncode == 0

    # Second run should update the version in the config
    with open(complex_temp_path.joinpath("moccasin.toml"), "w") as f:
        f.write(COMPLEX_UPDATE_PACKAGES_TOML)

    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        result_two = subprocess.run(
            [mox_path, "build", "BuyMeACoffee.vy", "--update-packages"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)

    project_root: Path = Config.find_project_root(complex_temp_path)
    config = Config(project_root)

    assert f"{PIP_PACKAGE_NAME}=={NEW_VERSION}" in config.dependencies
    assert f"{PATRICK_PACKAGE_NAME}" in config.dependencies
    assert complex_temp_path.joinpath(LIB_GH_PATH).exists()
    assert complex_temp_path.joinpath(LIB_PIP_PATH).exists()
    assert "Done compiling BuyMeACoffee" in result_two.stderr
    assert result_two.returncode == 0
