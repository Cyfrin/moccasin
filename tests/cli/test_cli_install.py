from pathlib import Path
import os
import subprocess
from tests.conftest import (
    COMPLEX_PROJECT_PATH,
)
from gaboon.constants.vars import PACKAGE_VERSION_FILE, DEPENDENCIES_FOLDER

package_to_install = "pcaversaccio/snekmate"


def test_run_help(gab_path):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [gab_path, "install", "-h"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Gaboon CLI install" in result.stdout


def test_install_snekmate(cleanup_dependencies_folder, gab_path):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [gab_path, "install", package_to_install],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Version not provided" in result.stderr
    assert f"Installed {package_to_install}" in result.stderr
    assert (
        Path(COMPLEX_PROJECT_PATH)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{package_to_install}")
        .exists()
    )
    assert (
        Path(COMPLEX_PROJECT_PATH)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{PACKAGE_VERSION_FILE}")
        .exists()
    )


def test_double_install_snekmate(cleanup_dependencies_folder, gab_path):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        subprocess.run(
            [gab_path, "install", package_to_install],
            check=True,
            capture_output=True,
            text=True,
        )
        result = subprocess.run(
            [gab_path, "install", package_to_install],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "already installed" in result.stderr
    assert (
        Path(COMPLEX_PROJECT_PATH)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{package_to_install}")
        .exists()
    )
    assert (
        Path(COMPLEX_PROJECT_PATH)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{PACKAGE_VERSION_FILE}")
        .exists()
    )
