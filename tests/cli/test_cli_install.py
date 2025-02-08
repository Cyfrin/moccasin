import os
import subprocess
from pathlib import Path

from tests.constants import (
    GITHUB_PACKAGE_NAME,
    LIB_GH_PATH,
    LIB_PIP_PATH,
    MOCCASIN_LIB_NAME,
    PATRICK_PACKAGE_NAME,
    PIP_PACKAGE_NAME,
    VERSIONS_TOML,
)


def test_run_help(mox_path, installation_cleanup_dependencies, installation_temp_path):
    current_dir = Path.cwd()
    try:
        os.chdir(installation_temp_path)
        result = subprocess.run(
            [mox_path, "install", "-h"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "Moccasin CLI install" in result.stdout


def test_run_install_no_dependencies(mox_path, installation_temp_path: Path):
    current_dir = Path.cwd()
    try:
        os.chdir(installation_temp_path)
        result = subprocess.run(
            [mox_path, "install"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    print_statements = result.stderr.split("\n")

    breakpoint()

    # assert "Installing 2 pip packages..." in print_statements
    # assert "Installing 2 GitHub packages..." in print_statements
    # assert installation_temp_path.joinpath("moccasin.toml").exists()


def test_run_install(
    mox_path, installation_cleanup_dependencies, installation_temp_path: Path
):
    current_dir = Path.cwd()
    try:
        os.chdir(installation_temp_path)
        result = subprocess.run(
            [mox_path, "install"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    print_statements = result.stderr.split("\n")

    gh_dir_path = installation_temp_path.joinpath(LIB_GH_PATH)
    pip_dir_path = installation_temp_path.joinpath(LIB_PIP_PATH)

    assert "Installing 2 pip packages..." in print_statements
    assert "Installing 2 GitHub packages..." in print_statements
    assert installation_temp_path.joinpath("moccasin.toml").exists()

    assert gh_dir_path.joinpath(PATRICK_PACKAGE_NAME).exists()
    assert gh_dir_path.joinpath(GITHUB_PACKAGE_NAME).exists()

    assert pip_dir_path.joinpath(PIP_PACKAGE_NAME).exists()
    assert pip_dir_path.joinpath(MOCCASIN_LIB_NAME).exists()

    assert gh_dir_path.joinpath(VERSIONS_TOML).exists()
    assert pip_dir_path.joinpath(VERSIONS_TOML).exists()


# os.listdir(installation_temp_path.joinpath(LIB_GH_PATH))
