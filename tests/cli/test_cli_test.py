import os
import subprocess
from pathlib import Path

import tomli_w

from moccasin.config import Config
from tests.constants import (
    LIB_GH_PATH,
    LIB_PIP_PATH,
    MOCCASIN_TOML,
    NEW_VERSION,
    PATRICK_PACKAGE_NAME,
    PIP_PACKAGE_NAME,
)
from tests.utils.helpers import (
    get_temp_versions_toml_from_libs,
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


def test_basic(mox_path, complex_temp_path, anvil):
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


def test_staging_flag_live_networks_and_update(mox_path, complex_temp_path, anvil):
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

    # Second run should update the version in the config
    # @dev issue with import file mismatch if we import Patrick package
    dependencies = [f"{PIP_PACKAGE_NAME}=={NEW_VERSION}"]
    old_moccasin_toml = rewrite_temp_moccasin_toml_dependencies(
        complex_temp_path, dependencies
    )

    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        result_two = subprocess.run(
            [mox_path, "test", "--network", "anvil", "--update-packages"],
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)

    assert not complex_temp_path.joinpath(LIB_GH_PATH).exists()
    assert complex_temp_path.joinpath(LIB_PIP_PATH).exists()

    project_root: Path = Config.find_project_root(complex_temp_path)
    config = Config(project_root)
    assert f"{PIP_PACKAGE_NAME}=={NEW_VERSION}" in config.dependencies
    assert f"{PATRICK_PACKAGE_NAME}" not in config.dependencies

    github_versions, pip_versions = get_temp_versions_toml_from_libs(complex_temp_path)
    assert not bool(github_versions)
    assert pip_versions[f"{PIP_PACKAGE_NAME}"] == f"=={NEW_VERSION}"

    # Check for the error message in the output
    assert result_two.returncode == 0
    assert "2 passed" in result_two.stdout
    assert "7 skipped" in result_two.stdout

    # Reset toml to the original for next test
    with open(complex_temp_path.joinpath(MOCCASIN_TOML), "wb") as f:
        tomli_w.dump(old_moccasin_toml, f)


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
