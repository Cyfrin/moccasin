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
from tests.constants import (
    PACKAGE_VERSION,
    PATRICK_ORG_NAME,
    PATRICK_PACKAGE_NAME,
    PIP_PACKAGE_NAME,
)


def test_can_purge_github_no_version(
    purge_temp_path, purge_reset_dependencies, mox_path
):
    current_dir = Path.cwd()
    try:
        os.chdir(purge_temp_path)
        result = subprocess.run(
            [mox_path, "purge", f"{PATRICK_PACKAGE_NAME}"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert f"Removed {PATRICK_PACKAGE_NAME}" in result.stderr
    project_root: Path = Config.find_project_root(Path(purge_temp_path))
    config = Config(project_root)
    assert f"{PATRICK_PACKAGE_NAME}@{PACKAGE_VERSION}" not in config.dependencies
    assert (
        not Path(purge_temp_path)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{GITHUB}/{PATRICK_ORG_NAME}")
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
            [mox_path, "purge", f"{PATRICK_PACKAGE_NAME}@{PACKAGE_VERSION}"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert f"Removed {PATRICK_PACKAGE_NAME}" in result.stderr
    project_root: Path = Config.find_project_root(Path(purge_temp_path))
    config = Config(project_root)
    assert f"{PATRICK_PACKAGE_NAME}@{PACKAGE_VERSION}" not in config.dependencies
    assert (
        not Path(purge_temp_path)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{GITHUB}/{PATRICK_ORG_NAME}")
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
            [mox_path, "purge", PIP_PACKAGE_NAME],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert f"Removed {PIP_PACKAGE_NAME}" in result.stderr
    project_root: Path = Config.find_project_root(Path(purge_temp_path))
    config = Config(project_root)
    assert PIP_PACKAGE_NAME not in config.dependencies
    assert (
        not Path(purge_temp_path)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{PYPI}/{PIP_PACKAGE_NAME}")
        .exists()
    )
