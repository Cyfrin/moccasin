import os
import subprocess
from pathlib import Path

import pytest
import tomli_w
from packaging.requirements import Requirement

from moccasin.config import Config
from tests.constants import (
    GITHUB_PACKAGE_NAME,
    LIB_GH_PATH,
    LIB_PIP_PATH,
    MOCCASIN_TOML,
    NEW_VERSION,
    PIP_PACKAGE_NAME,
    VERSION,
)
from tests.utils.helpers import (
    get_temp_versions_toml_gh,
    rewrite_temp_moccasin_toml_dependencies,
)

EXPECTED_HELP_TEXT = "Runs pytest"


def test_test_help(mox_path):
    result = subprocess.run(
        [mox_path, "test", "-h"], check=True, capture_output=True, text=True
    )
    assert EXPECTED_HELP_TEXT in result.stdout, (
        "Help output does not contain expected text"
    )
    assert result.returncode == 0


def test_basic(
    mox_path,
    complex_temp_path,
    complex_cleanup_out_folder,
    complex_cleanup_dependencies_folder,
    anvil,
):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        result = subprocess.run([mox_path, "test"], capture_output=True, text=True)
    finally:
        os.chdir(current_dir)

    assert result.returncode == 0

    # Check for the error message in the output
    assert "8 passed" in result.stdout
    assert "1 skipped" in result.stdout


# @dev test adapted to the ordering of dependencies
@pytest.mark.parametrize(
    "cli_args, rewrite_dependencies, expected_lib_path, expected_pip_deps, expected_gh_deps, expected_gh_versions",
    [
        # --no-install should skip package installation
        (["--no-install"], [], False, ["snekmate==0.1.0"], [], None),
        # Default behavior - installs dependencies
        (
            [],
            [f"{GITHUB_PACKAGE_NAME}@{NEW_VERSION}", f"{PIP_PACKAGE_NAME}>={VERSION}"],
            True,
            [f"{PIP_PACKAGE_NAME}>={VERSION}"],
            [f"{GITHUB_PACKAGE_NAME}@{NEW_VERSION}"],
            {f"{GITHUB_PACKAGE_NAME}": NEW_VERSION},
        ),
        # Change compiled file
        ([], [], True, ["snekmate==0.1.0"], [], None),
    ],
)
def test_test_basic_with_flags(
    complex_temp_path,
    complex_cleanup_out_folder,
    complex_cleanup_dependencies_folder,
    mox_path,
    anvil,
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
        base_args = [mox_path, "test"]
        result = subprocess.run(base_args + cli_args, capture_output=True, text=True)
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
    print(config.dependencies)
    print(expected_pip_deps + expected_gh_deps)
    assert config.dependencies == expected_pip_deps + expected_gh_deps

    # Verify gh versions file contents
    if expected_gh_versions:
        github_versions = get_temp_versions_toml_gh(complex_temp_path)
        assert github_versions == expected_gh_versions

    # Check for the error message in the output
    assert "8 passed" in result.stdout
    assert "1 skipped" in result.stdout

    # Reset toml to the original for next test
    with open(complex_temp_path.joinpath(MOCCASIN_TOML), "wb") as f:
        tomli_w.dump(old_moccasin_toml, f)


def test_test_complex_project_has_no_warnings(
    complex_cleanup_out_folder, complex_temp_path, mox_path
):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        result = subprocess.run(
            [mox_path, "test"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "PytestAssertRewriteWarning" not in result.stdout
    assert result.returncode == 0


def test_test_complex_project_passes_pytest_flags(
    complex_cleanup_out_folder, complex_temp_path, mox_path
):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        result = subprocess.run(
            [mox_path, "test", "-k", "test_increment_two"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "1 passed" in result.stdout
    assert "8 deselected" in result.stdout
    assert result.returncode == 0


def test_test_coverage(
    complex_cleanup_out_folder, complex_cleanup_coverage, complex_temp_path, mox_path
):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        result = subprocess.run(
            [mox_path, "test", "--coverage"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "coverage:" in result.stdout
    assert "Computation" not in result.stdout
    assert current_dir.joinpath(complex_temp_path).joinpath(".coverage").exists()


def test_test_gas(
    complex_cleanup_out_folder, complex_cleanup_coverage, complex_temp_path, mox_path
):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        result = subprocess.run(
            [mox_path, "test", "--gas-profile"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Computation" in result.stdout
    assert "coverage:" not in result.stdout


def test_staging_flag_live_networks(mox_path, complex_temp_path, anvil):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        result = subprocess.run(
            [mox_path, "test", "--network", "anvil"], capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)

    assert result.returncode == 0

    # Check for the error message in the output
    assert "2 passed" in result.stdout
    assert "7 skipped" in result.stdout


def test_xdist_auto(mox_path, test_config_temp_path):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(test_config_temp_path))
        result = subprocess.run(
            [mox_path, "test", "-nauto"], capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)

    assert result.returncode == 0
    assert "workers" in result.stdout
    assert ".." in result.stdout


def test_xdist_num(mox_path, test_config_temp_path):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(test_config_temp_path))
        result = subprocess.run(
            [mox_path, "test", "-n", "5"], capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert result.returncode == 0
    assert "5/5 workers" in result.stdout
    assert ".." in result.stdout


def test_test_v(mox_path, test_config_temp_path):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(test_config_temp_path))
        result = subprocess.run(
            [mox_path, "test", "-vvv"], capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert result.returncode == 0
    assert "PASSED" in result.stdout
    assert "tests/test_fuzz_counter.py::fuzzer::runTest" in result.stdout
