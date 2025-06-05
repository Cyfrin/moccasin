import os
import subprocess
from pathlib import Path

import pytest

from moccasin.commands.install import GITHUB, PYPI
from moccasin.config import Config
from moccasin.constants.vars import DEPENDENCIES_FOLDER
from tests.constants import (
    COMMENT_CONTENT,
    GITHUB_PACKAGE_NAME,
    LIB_GH_PATH,
    LIB_PIP_PATH,
    MOCCASIN_LIB_NAME,
    MOCCASIN_TOML,
    ORG_NAME,
    PACKAGE_NEW_VERSION,
    PACKAGE_VERSION,
    PATRICK_PACKAGE_NAME,
    PIP_PACKAGE_NAME,
    VERSIONS_TOML,
)
from tests.utils.helpers import get_temp_versions_toml_gh


def test_install_without_parameters_installs_packages_in_toml(
    installation_temp_path, installation_cleanup_dependencies, mox_path
):
    current_dir = Path.cwd()
    try:
        os.chdir(installation_temp_path)
        result = subprocess.run(
            [mox_path, "install"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert f"+ {PIP_PACKAGE_NAME}=={PACKAGE_VERSION}" in result.stderr
    assert (
        Path(installation_temp_path)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{PYPI}/{PIP_PACKAGE_NAME}")
        .exists()
    )


def test_double_install_snekmate(
    installation_temp_path, installation_cleanup_dependencies, mox_path
):
    current_dir = Path.cwd()
    try:
        os.chdir(installation_temp_path)
        result_one = subprocess.run(
            [mox_path, "install", GITHUB_PACKAGE_NAME],
            check=True,
            capture_output=True,
            text=True,
        )
        result_two = subprocess.run(
            [mox_path, "install", GITHUB_PACKAGE_NAME],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert result_one.returncode == 0
    assert result_two.returncode == 0
    assert (
        Path(installation_temp_path)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{GITHUB}/{ORG_NAME}")
        .exists()
    )


def test_write_to_config_after_install(
    installation_temp_path, installation_cleanup_dependencies, mox_path
):
    project_root: Path = Config.find_project_root(Path(installation_temp_path))
    config = Config(project_root)
    starting_dependencies = config.dependencies
    assert GITHUB_PACKAGE_NAME not in config.dependencies

    # Arrange
    current_dir = Path.cwd()
    # Act
    try:
        os.chdir(installation_temp_path)
        subprocess.run(
            [mox_path, "install", GITHUB_PACKAGE_NAME],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    # Assert
    project_root: Path = Config.find_project_root(Path(installation_temp_path))
    config = Config(project_root)
    assert GITHUB_PACKAGE_NAME in config.dependencies
    for dep in starting_dependencies:
        assert dep in config.dependencies
    assert COMMENT_CONTENT in config.read_configs_preserve_comments().as_string()


def test_can_install_with_version(
    installation_temp_path, installation_cleanup_dependencies, mox_path
):
    current_dir = Path.cwd()
    try:
        os.chdir(installation_temp_path)
        result = subprocess.run(
            [mox_path, "install", f"{GITHUB_PACKAGE_NAME}@{PACKAGE_VERSION}"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert f"Installed {GITHUB_PACKAGE_NAME}" in result.stderr
    project_root: Path = Config.find_project_root(Path(installation_temp_path))
    config = Config(project_root)
    assert f"{GITHUB_PACKAGE_NAME}@{PACKAGE_VERSION}" in config.dependencies
    assert (
        Path(installation_temp_path)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{GITHUB}/{ORG_NAME}")
        .exists()
    )


def test_can_change_versions(
    installation_temp_path, installation_cleanup_dependencies, mox_path
):
    current_dir = Path.cwd()
    try:
        os.chdir(installation_temp_path)
        result_one = subprocess.run(
            [mox_path, "install", f"{GITHUB_PACKAGE_NAME}@{PACKAGE_VERSION}"],
            check=True,
            capture_output=True,
            text=True,
        )
        result_two = subprocess.run(
            [mox_path, "install", f"{GITHUB_PACKAGE_NAME}@{PACKAGE_NEW_VERSION}"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert f"Installed {GITHUB_PACKAGE_NAME}" in result_one.stderr
    assert f"Updating {GITHUB_PACKAGE_NAME}" in result_two.stderr
    project_root: Path = Config.find_project_root(Path(installation_temp_path))
    config = Config(project_root)
    assert f"{GITHUB_PACKAGE_NAME}@{PACKAGE_NEW_VERSION}" in config.dependencies
    assert (
        Path(installation_temp_path)
        .joinpath(f"{DEPENDENCIES_FOLDER}/{GITHUB}/{ORG_NAME}")
        .exists()
    )


def test_can_compile_with_github_search_path(
    installation_temp_path, installation_cleanup_dependencies, mox_path
):
    current_dir = Path.cwd()
    try:
        os.chdir(installation_temp_path)
        result_install = subprocess.run(
            [mox_path, "install", PATRICK_PACKAGE_NAME],
            check=True,
            capture_output=True,
            text=True,
        )
        result_compile = subprocess.run(
            [mox_path, "compile"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "Done compiling project!" in result_compile.stderr
    assert result_install.returncode == 0
    assert result_compile.returncode == 0


def test_no_moccasin_toml_saves_dependencies_to_pyproject(
    mox_path, no_config_temp_path, no_config_config
):
    current_dir = Path.cwd()
    try:
        os.chdir(no_config_temp_path)
        result_install = subprocess.run(
            [mox_path, "install", PATRICK_PACKAGE_NAME],
            check=True,
            capture_output=True,
            text=True,
        )
        result_compile = subprocess.run(
            [mox_path, "compile"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert no_config_config.read_pyproject_config() == {
        "project": {
            "dot_env": ".hello",
            "src": "contracts",
            "dependencies": ["patrickalphac/test_repo"],
        }
    }

    with open(no_config_temp_path.joinpath("pyproject.toml")) as f:
        assert "patrickalphac/test_repo" in f.read()
    assert "Done compiling project!" in result_compile.stderr
    assert result_install.returncode == 0
    assert result_compile.returncode == 0

    project_root: Path = Config.find_project_root(Path(no_config_temp_path))
    config = Config(project_root)
    assert PATRICK_PACKAGE_NAME in config.dependencies


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

    assert "Installing 2 pip packages..." in result.stderr

    assert installation_temp_path.joinpath(MOCCASIN_TOML).exists()
    assert installation_temp_path.joinpath(LIB_GH_PATH).exists()
    assert not any(installation_temp_path.joinpath(LIB_GH_PATH).iterdir())

    assert installation_temp_path.joinpath(LIB_PIP_PATH).exists()
    assert any(installation_temp_path.joinpath(LIB_PIP_PATH).iterdir())


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

    assert "Installing 2 GitHub packages..." in result.stderr

    assert installation_temp_path.joinpath(MOCCASIN_TOML).exists()
    assert installation_temp_path.joinpath(LIB_GH_PATH).exists()
    assert any(installation_temp_path.joinpath(LIB_GH_PATH).iterdir())

    assert installation_temp_path.joinpath(LIB_PIP_PATH).exists()
    assert not any(installation_temp_path.joinpath(LIB_PIP_PATH).iterdir())


def test_run_install_all_dependencies(
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

    gh_dir_path = installation_temp_path.joinpath(LIB_GH_PATH)
    pip_dir_path = installation_temp_path.joinpath(LIB_PIP_PATH)

    assert "Installing 2 pip packages..." in result.stderr
    assert "Installing 1 GitHub packages..." in result.stderr
    assert installation_temp_path.joinpath(MOCCASIN_TOML).exists()
    assert gh_dir_path.exists()
    assert any(gh_dir_path.iterdir())
    assert gh_dir_path.joinpath(VERSIONS_TOML).exists()
    assert gh_dir_path.joinpath(PATRICK_PACKAGE_NAME).exists()

    assert pip_dir_path.exists()
    assert any(pip_dir_path.iterdir())
    assert pip_dir_path.joinpath(PIP_PACKAGE_NAME).exists()
    assert pip_dir_path.joinpath(MOCCASIN_LIB_NAME).exists()


def test_run_install_update_pip_and_gh(
    mox_path,
    installation_cleanup_dependencies,
    installation_temp_path: Path,
    installation_keep_full_dependencies,
):
    current_dir = Path.cwd()
    try:
        os.chdir(installation_temp_path)
        # Run install one time to get all dependencies
        subprocess.run(
            [mox_path, "install"], check=True, capture_output=True, text=True
        )
        # Run install again to update dependencies
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
    gh_message = f"Updated {GITHUB_PACKAGE_NAME}@{PACKAGE_NEW_VERSION}"
    pip_message = f"Updated package: {PIP_PACKAGE_NAME}=={PACKAGE_NEW_VERSION}"

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


@pytest.mark.parametrize(
    "dependencies_to_add, expected_dependencies, expected_gh_versions",
    [
        # Default moccasin.toml install
        (
            [],
            ["snekmate", "moccasin", "PatrickAlphaC/test_repo"],
            {"patrickalphac/test_repo": "0.1.2"},
        ),
        # Change pip specification
        (
            [f"{PIP_PACKAGE_NAME}>={PACKAGE_VERSION}", f"{MOCCASIN_LIB_NAME}==0.3.6"],
            [
                "PatrickAlphaC/test_repo",
                f"{PIP_PACKAGE_NAME}>={PACKAGE_VERSION}",
                f"{MOCCASIN_LIB_NAME}==0.3.6",
            ],
            {"patrickalphac/test_repo": "0.1.2"},
        ),
        # Change gh specification
        (
            [f"{PATRICK_PACKAGE_NAME}@0.1.0"],
            [
                f"{PIP_PACKAGE_NAME}>={PACKAGE_VERSION}",
                f"{MOCCASIN_LIB_NAME}==0.3.6",
                "patrickalphac/test_repo@0.1.0",
            ],
            {"patrickalphac/test_repo": "0.1.0"},
        ),
    ],
)
def test_run_multiple_install(
    mox_path,
    installation_temp_path: Path,
    dependencies_to_add,
    expected_dependencies,
    expected_gh_versions,
):
    current_dir = Path.cwd()
    try:
        os.chdir(installation_temp_path)
        base_command = [mox_path, "install"]
        subprocess.run(
            base_command + dependencies_to_add,
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)

    gh_dir_path = installation_temp_path.joinpath(LIB_GH_PATH)
    pip_dir_path = installation_temp_path.joinpath(LIB_PIP_PATH)

    assert installation_temp_path.joinpath(MOCCASIN_TOML).exists()
    assert gh_dir_path.joinpath(PATRICK_PACKAGE_NAME).exists()
    assert pip_dir_path.joinpath(PIP_PACKAGE_NAME).exists()
    assert pip_dir_path.joinpath(MOCCASIN_LIB_NAME).exists()

    # Verify config state if versions are expected
    project_root: Path = Config.find_project_root(installation_temp_path)
    config = Config(project_root)
    assert config.dependencies == expected_dependencies

    # Verify versions file contents
    github_versions = get_temp_versions_toml_gh(installation_temp_path)
    assert github_versions == expected_gh_versions
