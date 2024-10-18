import os
import subprocess
from pathlib import Path

from moccasin.config import Config
from moccasin.constants.vars import (
    DEPENDENCIES_FOLDER,
    GITHUB,
    PACKAGE_VERSION_FILE,
    PYPI,
)
from tests.conftest import (
    patrick_org_name,
    patrick_package_name,
    pip_package_name,
    version,
)


def test_can_purge_github_no_version(
    purge_temp_path, purge_reset_dependencies, mox_path
):
    current_dir = Path.cwd()
    try:
        os.chdir(purge_temp_path)
        result = subprocess.run(
            [mox_path, "purge", f"{patrick_package_name}"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert f"Removed {patrick_package_name}" in result.stderr
    project_root: Path = Config.find_project_root(Path(purge_temp_path))
    config = Config(project_root)
    assert f"{patrick_package_name}@{version}" not in config.dependencies
    assert (
        not Path(purge_temp_path)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{GITHUB}/{patrick_org_name}")
        .exists()
    )
    versions_file = (
        purge_temp_path.joinpath(DEPENDENCIES_FOLDER)
        .joinpath(GITHUB)
        .joinpath(PACKAGE_VERSION_FILE)
    )
    with open(versions_file) as f:
        assert f.read() == ""


def test_can_purge_github_with_version(
    purge_temp_path, purge_reset_dependencies, mox_path
):
    current_dir = Path.cwd()
    try:
        os.chdir(purge_temp_path)
        result = subprocess.run(
            [mox_path, "purge", f"{patrick_package_name}@{version}"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert f"Removed {patrick_package_name}" in result.stderr
    project_root: Path = Config.find_project_root(Path(purge_temp_path))
    config = Config(project_root)
    assert f"{patrick_package_name}@{version}" not in config.dependencies
    assert (
        not Path(purge_temp_path)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{GITHUB}/{patrick_org_name}")
        .exists()
    )
    versions_file = (
        purge_temp_path.joinpath(DEPENDENCIES_FOLDER)
        .joinpath(GITHUB)
        .joinpath(PACKAGE_VERSION_FILE)
    )
    with open(versions_file) as f:
        assert f.read() == ""


def test_can_purge_pip(purge_temp_path, purge_reset_dependencies, mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(purge_temp_path)
        result = subprocess.run(
            [mox_path, "purge", pip_package_name],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert f"Removed {pip_package_name}" in result.stderr
    project_root: Path = Config.find_project_root(Path(purge_temp_path))
    config = Config(project_root)
    assert pip_package_name not in config.dependencies
    assert (
        not Path(purge_temp_path)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{PYPI}/{pip_package_name}")
        .exists()
    )
