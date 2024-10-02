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
    PURGE_PROJECT_PATH,
    patrick_org_name,
    patrick_package_name,
    pip_package_name,
    version,
)


def test_can_purge_github_no_version(purge_reset_dependencies, mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(PURGE_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "purge", f"{patrick_package_name}"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert f"Removed {patrick_package_name}" in result.stderr
    project_root: Path = Config.find_project_root(Path(PURGE_PROJECT_PATH))
    config = Config(project_root)
    assert f"{patrick_package_name}@{version}" not in config.dependencies
    assert (
        not Path(PURGE_PROJECT_PATH)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{GITHUB}/{patrick_org_name}")
        .exists()
    )
    versions_file = (
        PURGE_PROJECT_PATH.joinpath(DEPENDENCIES_FOLDER)
        .joinpath(GITHUB)
        .joinpath(PACKAGE_VERSION_FILE)
    )
    with open(versions_file) as f:
        assert f.read() == ""


def test_can_purge_github_with_version(purge_reset_dependencies, mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(PURGE_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "purge", f"{patrick_package_name}@{version}"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert f"Removed {patrick_package_name}" in result.stderr
    project_root: Path = Config.find_project_root(Path(PURGE_PROJECT_PATH))
    config = Config(project_root)
    assert f"{patrick_package_name}@{version}" not in config.dependencies
    assert (
        not Path(PURGE_PROJECT_PATH)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{GITHUB}/{patrick_org_name}")
        .exists()
    )
    versions_file = (
        PURGE_PROJECT_PATH.joinpath(DEPENDENCIES_FOLDER)
        .joinpath(GITHUB)
        .joinpath(PACKAGE_VERSION_FILE)
    )
    with open(versions_file) as f:
        assert f.read() == ""


def test_can_purge_pip(purge_reset_dependencies, mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(PURGE_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "purge", pip_package_name],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert f"Removed {pip_package_name}" in result.stderr
    project_root: Path = Config.find_project_root(Path(PURGE_PROJECT_PATH))
    config = Config(project_root)
    assert pip_package_name not in config.dependencies
    assert (
        not Path(PURGE_PROJECT_PATH)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{PYPI}/{pip_package_name}")
        .exists()
    )
