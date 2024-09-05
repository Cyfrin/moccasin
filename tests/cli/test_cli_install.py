from pathlib import Path
import os
import subprocess
from tests.conftest import (
    INSTALL_PROJECT_PATH,
)
from gaboon.constants.vars import DEPENDENCIES_FOLDER

package_name = "snekmate"
package_to_install = f"pcaversaccio/{package_name}"


def test_run_help(gab_path):
    current_dir = Path.cwd()
    try:
        os.chdir(INSTALL_PROJECT_PATH)
        result = subprocess.run(
            [gab_path, "install", "-h"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Gaboon CLI install" in result.stdout


def test_install_snekmate(complex_cleanup_dependencies_folder, gab_path):
    current_dir = Path.cwd()
    try:
        os.chdir(INSTALL_PROJECT_PATH)
        result = subprocess.run(
            [gab_path, "install", package_to_install],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert f"Installed {package_name}" in result.stderr
    assert (
        Path(INSTALL_PROJECT_PATH)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{package_name}")
        .exists()
    )


def test_double_install_snekmate(complex_cleanup_dependencies_folder, gab_path):
    current_dir = Path.cwd()
    try:
        os.chdir(INSTALL_PROJECT_PATH)
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
    assert "Audited 1 package" in result.stderr
    assert (
        Path(INSTALL_PROJECT_PATH)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{package_name}")
        .exists()
    )
