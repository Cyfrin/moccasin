import os
import subprocess
from pathlib import Path

EXPECTED_HELP_TEXT = "Vyper compiler"


def test_compile_help(mox_path):
    result = subprocess.run(
        [mox_path, "compile", "-h"], check=True, capture_output=True, text=True
    )
    assert (
        EXPECTED_HELP_TEXT in result.stdout
    ), "Help output does not contain expected text"
    assert result.returncode == 0


def test_build_help(mox_path):
    result = subprocess.run(
        [mox_path, "build", "-h"], check=True, capture_output=True, text=True
    )
    assert (
        EXPECTED_HELP_TEXT in result.stdout
    ), "Help output does not contain expected text"
    assert result.returncode == 0


def test_compile_alias_build_project(
    complex_temp_path, complex_cleanup_out_folder, mox_path
):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        result = subprocess.run(
            [mox_path, "build"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "Running compile command" in result.stderr
    assert result.returncode == 0


def test_compile_one(complex_temp_path, complex_cleanup_out_folder, mox_path):
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
    assert "Done compiling BuyMeACoffee" in result.stderr
    assert result.returncode == 0
