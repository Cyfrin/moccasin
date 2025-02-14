import os
import subprocess
from pathlib import Path

import pytest
import tomli_w

from moccasin.config import Config
from tests.constants import (
    LIB_GH_PATH,
    LIB_PIP_PATH,
    MOCCASIN_TOML,
    NEW_VERSION,
    PATRICK_PACKAGE_NAME,
    PIP_PACKAGE_NAME,
    VERSION,
)
from tests.utils.helpers import (
    get_temp_versions_toml_from_libs,
    rewrite_temp_moccasin_toml_dependencies,
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


@pytest.mark.parametrize(
    "cli_args, expect_gh_path, expect_pip_path, expect_pip_version, expect_gh_package, dependencies",
    [
        # --no-install should skip package installation
        (["--no-install"], False, False, f"=={VERSION}", False, []),
        # Default behavior - installs dependencies
        ([], False, True, f"=={VERSION}", False, []),
        # --update-packages should update existing dependencies
        (["--update-packages"], True, True, f"=={NEW_VERSION}", True, None),
    ],
)
def test_compile_with_flags(
    complex_temp_path,
    complex_cleanup_dependencies_folder,
    mox_path,
    cli_args,
    expect_gh_path,
    expect_pip_path,
    expect_pip_version,
    expect_gh_package,
    dependencies,
):
    current_dir = Path.cwd()
    if dependencies is not None:
        old_moccasin_toml = rewrite_temp_moccasin_toml_dependencies(
            complex_temp_path, dependencies
        )
    else:
        old_moccasin_toml = rewrite_temp_moccasin_toml_dependencies(complex_temp_path)

    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        base_args = [mox_path, "build", "BuyMeACoffee.vy"]
        result = subprocess.run(
            base_args + cli_args, check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)

    assert complex_temp_path.joinpath(LIB_GH_PATH).exists() == expect_gh_path
    assert complex_temp_path.joinpath(LIB_PIP_PATH).exists() == expect_pip_path

    # Verify config state if versions are expected
    project_root: Path = Config.find_project_root(complex_temp_path)
    config = Config(project_root)
    github_versions, pip_versions = get_temp_versions_toml_from_libs(complex_temp_path)
    assert f"{PIP_PACKAGE_NAME}{expect_pip_version}" in config.dependencies
    if expect_pip_path and expect_pip_version:
        assert pip_versions[f"{PIP_PACKAGE_NAME}"] == expect_pip_version
    if expect_gh_path and expect_gh_package:
        assert PATRICK_PACKAGE_NAME in config.dependencies
        assert github_versions[f"{PATRICK_PACKAGE_NAME}"] == "0.1.1"

    assert "Done compiling BuyMeACoffee" in result.stderr
    assert result.returncode == 0

    # Reset toml to the original for next test
    with open(complex_temp_path.joinpath(MOCCASIN_TOML), "wb") as f:
        tomli_w.dump(old_moccasin_toml, f)
