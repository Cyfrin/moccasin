import os
import subprocess
from pathlib import Path

import pytest
import tomli_w
from packaging.requirements import Requirement

from moccasin.config import Config
from tests.constants import (
    LIB_GH_PATH,
    LIB_PIP_PATH,
    MOCCASIN_LIB_NAME,
    MOCCASIN_TOML,
    PIP_PACKAGE_NAME,
    VERSION,
)
from tests.utils.helpers import (
    get_temp_versions_toml_gh,
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


# @dev test adapted to the ordering of dependencies
@pytest.mark.parametrize(
    "cli_args, rewrite_dependencies, expected_lib_path, expected_pip_deps, expected_gh_deps, expected_gh_versions",
    [
        # --no-install should skip package installation
        (["BuyMeACoffee.vy", "--no-install"], [], False, ["snekmate==0.1.0"], [], None),
        # Default behavior - installs dependencies
        (
            ["BuyMeACoffee.vy"],
            [
                "PatrickAlphaC/test_repo",
                f"{PIP_PACKAGE_NAME}>={VERSION}",
                f"{MOCCASIN_LIB_NAME}==0.3.6",
            ],
            True,
            [f"{PIP_PACKAGE_NAME}>={VERSION}", f"{MOCCASIN_LIB_NAME}==0.3.6"],
            ["PatrickAlphaC/test_repo"],
            {"patrickalphac/test_repo": "0.1.1"},
        ),
        # Change compiled file
        (["MyTokenPyPI.vy"], [], True, ["snekmate==0.1.0"], [], None),
    ],
)
def test_compile_with_flags(
    complex_temp_path,
    complex_cleanup_out_folder,
    complex_cleanup_dependencies_folder,
    mox_path,
    cli_args,
    rewrite_dependencies,
    expected_lib_path,
    expected_pip_deps,
    expected_gh_deps,
    expected_gh_versions,
):
    current_dir = Path.cwd()
    old_moccasin_toml = rewrite_temp_moccasin_toml_dependencies(
        complex_temp_path, rewrite_dependencies
    )

    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        base_args = [mox_path, "build"]
        result = subprocess.run(
            base_args + cli_args, check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)

    assert complex_temp_path.joinpath(MOCCASIN_TOML).exists()

    gh_dir_path = complex_temp_path.joinpath(LIB_GH_PATH)
    pip_dir_path = complex_temp_path.joinpath(LIB_PIP_PATH)
    assert gh_dir_path.exists() == expected_lib_path
    assert pip_dir_path.exists() == expected_lib_path

    for dep in expected_pip_deps:
        pip_requirement = Requirement(dep)
        assert pip_dir_path.joinpath(pip_requirement.name).exists() == expected_lib_path
    if expected_gh_deps:
        for dep in expected_gh_deps:
            assert (
                gh_dir_path.joinpath(dep.lower().split("@")[0]).exists()
                == expected_lib_path
            )

    # Verify config state if versions are expected
    project_root: Path = Config.find_project_root(complex_temp_path)
    config = Config(project_root)
    assert config.dependencies == expected_pip_deps + expected_gh_deps

    # Verify gh versions file contents
    if expected_gh_versions:
        github_versions = get_temp_versions_toml_gh(complex_temp_path)
        assert github_versions == expected_gh_versions

    assert f"Done compiling {cli_args[0].replace('.vy', '')}" in result.stderr
    assert result.returncode == 0

    # Reset toml to the original for next test
    with open(complex_temp_path.joinpath(MOCCASIN_TOML), "wb") as f:
        tomli_w.dump(old_moccasin_toml, f)
