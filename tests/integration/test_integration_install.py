import os
import subprocess
from pathlib import Path

from moccasin.config import Config
from moccasin.constants.vars import DEPENDENCIES_FOLDER
from tests.conftest import INSTALL_PROJECT_PATH

pip_package_name = "snekmate"
org_name = "pcaversaccio"
github_package_name = f"{org_name}/{pip_package_name}"
version = "0.1.0"
new_version = "0.0.5"
comment_content = "PRESERVE COMMENTS"


def test_install_without_parameters_installs_packages_in_toml(
    installation_cleanup_dependencies, mox_path
):
    current_dir = Path.cwd()
    try:
        os.chdir(INSTALL_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "install"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert f"+ {pip_package_name}=={version}" in result.stderr
    assert (
        Path(INSTALL_PROJECT_PATH)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{pip_package_name}")
        .exists()
    )


def test_double_install_snekmate(installation_cleanup_dependencies, mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(INSTALL_PROJECT_PATH)
        result_one = subprocess.run(
            [mox_path, "install", github_package_name],
            check=True,
            capture_output=True,
            text=True,
        )
        result_two = subprocess.run(
            [mox_path, "install", github_package_name],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert result_one.returncode == 0
    assert result_two.returncode == 0
    assert (
        Path(INSTALL_PROJECT_PATH)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{org_name}")
        .exists()
    )


def test_write_to_config_after_install(installation_cleanup_dependencies, mox_path):
    project_root: Path = Config.find_project_root(Path(INSTALL_PROJECT_PATH))
    config = Config(project_root)
    starting_dependencies = config.dependencies
    assert github_package_name not in config.dependencies

    # Arrange
    current_dir = Path.cwd()
    # Act
    try:
        os.chdir(INSTALL_PROJECT_PATH)
        subprocess.run(
            [mox_path, "install", github_package_name],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    # Assert
    project_root: Path = Config.find_project_root(Path(INSTALL_PROJECT_PATH))
    config = Config(project_root)
    assert github_package_name in config.dependencies
    for dep in starting_dependencies:
        assert dep in config.dependencies
    assert (
        comment_content in config.read_moccasin_config_preserve_comments().as_string()
    )


def test_can_install_with_version(installation_cleanup_dependencies, mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(INSTALL_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "install", f"{github_package_name}@{version}"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert f"Installed {github_package_name}" in result.stderr
    project_root: Path = Config.find_project_root(Path(INSTALL_PROJECT_PATH))
    config = Config(project_root)
    assert f"{github_package_name}@{version}" in config.dependencies
    assert (
        Path(INSTALL_PROJECT_PATH)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{org_name}")
        .exists()
    )


def test_can_change_versions(installation_cleanup_dependencies, mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(INSTALL_PROJECT_PATH)
        result_one = subprocess.run(
            [mox_path, "install", f"{github_package_name}@{version}"],
            check=True,
            capture_output=True,
            text=True,
        )
        result_two = subprocess.run(
            [mox_path, "install", f"{github_package_name}@{new_version}"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert f"Installed {github_package_name}" in result_one.stderr
    assert f"Updating {github_package_name}" in result_two.stderr
    project_root: Path = Config.find_project_root(Path(INSTALL_PROJECT_PATH))
    config = Config(project_root)
    assert f"{github_package_name}@{new_version}" in config.dependencies
    assert (
        Path(INSTALL_PROJECT_PATH)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{org_name}")
        .exists()
    )
