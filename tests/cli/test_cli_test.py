import subprocess
import os
from tests.conftest import COMPLEX_PROJECT_PATH
from pathlib import Path

EXPECTED_HELP_TEXT = "Runs pytest"


def test_test_help(gab_path):
    result = subprocess.run(
        [gab_path, "test", "-h"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert (
        EXPECTED_HELP_TEXT in result.stdout
    ), "Help output does not contain expected text"
    assert result.returncode == 0


def test_test_complex_project_has_no_warnings(complex_cleanup_out_folder, gab_path):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(COMPLEX_PROJECT_PATH))
        result = subprocess.run(
            [gab_path, "test"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "PytestAssertRewriteWarning" not in result.stdout
    assert result.returncode == 0


def test_test_complex_project_passes_pytest_flags(complex_cleanup_out_folder, gab_path):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(COMPLEX_PROJECT_PATH))
        result = subprocess.run(
            [gab_path, "test", "-k", "test_increment_two"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "2 passed" not in result.stdout
    assert "1 passed" in result.stdout
    assert "2 deselected" in result.stdout
    assert result.returncode == 0
