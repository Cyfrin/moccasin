import os
import subprocess
from pathlib import Path

from tests.conftest import COMPLEX_PROJECT_PATH

EXPECTED_HELP_TEXT = "Runs pytest"


def test_test_help(mox_path):
    result = subprocess.run(
        [mox_path, "test", "-h"], check=True, capture_output=True, text=True
    )
    assert (
        EXPECTED_HELP_TEXT in result.stdout
    ), "Help output does not contain expected text"
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


def test_test_complex_project_has_no_warnings(complex_cleanup_out_folder, mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(COMPLEX_PROJECT_PATH))
        result = subprocess.run(
            [mox_path, "test"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "PytestAssertRewriteWarning" not in result.stdout
    assert result.returncode == 0


def test_test_complex_project_passes_pytest_flags(complex_cleanup_out_folder, mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(COMPLEX_PROJECT_PATH))
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


def test_test_coverage(complex_cleanup_out_folder, complex_cleanup_coverage, mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(COMPLEX_PROJECT_PATH))
        result = subprocess.run(
            [mox_path, "test", "--coverage"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "coverage:" in result.stdout
    assert "Computation" not in result.stdout
    assert current_dir.joinpath(COMPLEX_PROJECT_PATH).joinpath(".coverage").exists()


def test_test_gas(complex_cleanup_out_folder, complex_cleanup_coverage, mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(COMPLEX_PROJECT_PATH))
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
