import os
import subprocess
from pathlib import Path

from tests.constants import (
    GITHUB_PACKAGE_NAME,
    LIB_GH_PATH,
    LIB_PIP_PATH,
    MOCCASIN_LIB_NAME,
    MOCCASIN_TOML,
    NEW_VERSION,
    PATRICK_PACKAGE_NAME,
    PIP_PACKAGE_NAME,
    VERSION,
    VERSIONS_TOML,
)


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

    assert "No packages to install." in result.stderr

    assert installation_temp_path.joinpath(MOCCASIN_TOML).exists()
    assert not installation_temp_path.joinpath(LIB_GH_PATH).exists()
    assert not installation_temp_path.joinpath(LIB_PIP_PATH).exists()


def test_run_install_only_pip_dependencies(
    mox_path,
    installation_cleanup_dependencies,
    installation_temp_path: Path,
    installation_keep_pip_dependencies,
):
    current_dir = Path.cwd()
    try:
        os.chdir(installation_temp_path)
        result = subprocess.run(
            [mox_path, "install"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)

    assert "No GitHub packages to install" in result.stderr
    assert "Installing 2 pip packages..." in result.stderr

    assert installation_temp_path.joinpath(MOCCASIN_TOML).exists()
    assert not installation_temp_path.joinpath(LIB_GH_PATH).exists()
    assert installation_temp_path.joinpath(LIB_PIP_PATH).exists()


def test_run_install_only_gh_dependencies(
    mox_path,
    installation_cleanup_dependencies,
    installation_temp_path: Path,
    installation_keep_gh_dependencies,
):
    current_dir = Path.cwd()
    try:
        os.chdir(installation_temp_path)
        result = subprocess.run(
            [mox_path, "install"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)

    assert "No pip packages to install" in result.stderr
    assert "Installing 2 GitHub packages..." in result.stderr

    assert installation_temp_path.joinpath(MOCCASIN_TOML).exists()
    assert installation_temp_path.joinpath(LIB_GH_PATH).exists()
    assert not installation_temp_path.joinpath(LIB_PIP_PATH).exists()


def test_run_install(mox_path, installation_temp_path: Path):
    current_dir = Path.cwd()
    try:
        os.chdir(installation_temp_path)
        result = subprocess.run(
            [mox_path, "install"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)

    gh_dir_path = installation_temp_path.joinpath(LIB_GH_PATH)
    pip_dir_path = installation_temp_path.joinpath(LIB_PIP_PATH)

    assert "Installing 2 pip packages..." in result.stderr
    assert "Installing 1 GitHub packages..." in result.stderr
    assert installation_temp_path.joinpath(MOCCASIN_TOML).exists()

    assert gh_dir_path.joinpath(PATRICK_PACKAGE_NAME).exists()

    assert pip_dir_path.joinpath(PIP_PACKAGE_NAME).exists()
    assert pip_dir_path.joinpath(MOCCASIN_LIB_NAME).exists()

    assert gh_dir_path.joinpath(VERSIONS_TOML).exists()
    assert pip_dir_path.joinpath(VERSIONS_TOML).exists()


def test_run_install_update_pip_and_gh(
    mox_path,
    installation_cleanup_dependencies,
    installation_temp_path: Path,
    installation_keep_full_dependencies,
):
    current_dir = Path.cwd()
    try:
        os.chdir(installation_temp_path)
        result = subprocess.run(
            [mox_path, "install", "snekmate==0.0.5", "pcaversaccio/snekmate@0.0.5"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)

    gh_dir_path = installation_temp_path.joinpath(LIB_GH_PATH)
    pip_dir_path = installation_temp_path.joinpath(LIB_PIP_PATH)
    gh_message = f"{GITHUB_PACKAGE_NAME} needs to be updated from version {VERSION} to {NEW_VERSION}"
    pip_message = f"{PIP_PACKAGE_NAME} needs to be updated from version {VERSION} to {NEW_VERSION}"

    assert gh_message in result.stderr
    assert pip_message in result.stderr
    assert "Installing 1 GitHub packages..." in result.stderr
    assert "Installing 1 pip packages..." in result.stderr
    assert installation_temp_path.joinpath(MOCCASIN_TOML).exists()

    assert gh_dir_path.joinpath(PATRICK_PACKAGE_NAME).exists()
    assert gh_dir_path.joinpath(GITHUB_PACKAGE_NAME).exists()

    assert pip_dir_path.joinpath(PIP_PACKAGE_NAME).exists()
    assert pip_dir_path.joinpath(MOCCASIN_LIB_NAME).exists()

    assert gh_dir_path.joinpath(VERSIONS_TOML).exists()
    assert pip_dir_path.joinpath(VERSIONS_TOML).exists()
