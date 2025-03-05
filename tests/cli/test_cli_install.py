import os
import subprocess
from pathlib import Path

from tests.constants import LIB_GH_PATH, LIB_PIP_PATH, MOCCASIN_TOML


def test_run_help(mox_path, installation_temp_path):
    current_dir = Path.cwd()
    try:
        os.chdir(installation_temp_path)
        result = subprocess.run(
            [mox_path, "install", "-h"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "Moccasin CLI install" in result.stdout


def test_run_install_no_dependencies(
    mox_path,
    installation_cleanup_dependencies,
    installation_temp_path: Path,
    installation_remove_dependencies,
):
    current_dir = Path.cwd()
    try:
        os.chdir(installation_temp_path)
        result = subprocess.run(
            [mox_path, "install"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)

    assert "No dependencies to install" in result.stderr

    assert installation_temp_path.joinpath(MOCCASIN_TOML).exists()
    assert not installation_temp_path.joinpath(LIB_GH_PATH).exists()
    assert not installation_temp_path.joinpath(LIB_PIP_PATH).exists()
