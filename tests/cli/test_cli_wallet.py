import os
import subprocess
from pathlib import Path

from moccasin.constants.vars import MOCCASIN_KEYSTORES_FOLDER_NAME
from tests.constants import COMPLEX_PROJECT_PATH


def test_run_help(mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "wallet", "-h"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "Moccasin CLI wallet" in result.stdout


def test_run_keystore_location(mox_path, moccasin_home_folder):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "wallet", "keystore-location"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    # @dev using moccasin_home_folder fixture due to MOCCASIN_KEYSTORE_PATH
    # being modified during session tests in temporary directory
    assert (
        f"Keystore location: {moccasin_home_folder.joinpath(MOCCASIN_KEYSTORES_FOLDER_NAME)} (default location)"
        in result.stderr
    )


def test_run_keystore_location_custom(mox_path, custom_moccasin_keystore_path):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "wallet", "keystore-location"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert (
        f"Keystore location: {str(custom_moccasin_keystore_path)} (custom location)"
        in result.stderr
    )
