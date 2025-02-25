import os
import subprocess
from pathlib import Path

import pytest
import tomli_w
from packaging.requirements import Requirement

from moccasin.config import Config
from tests.constants import (
    LIB_GH_PATH,
    LIB_PIP_PATH,
    MOCCASIN_LIB_NAME,
    MOCCASIN_TOML,
    PIP_PACKAGE_NAME,
    VERSION,
)
from tests.utils.helpers import (
    get_temp_versions_toml_gh,
    rewrite_temp_moccasin_toml_dependencies,
)


# --------------------------------------------------------------
#                         WITHOUT ANVIL
# --------------------------------------------------------------
def test_deploy_price_feed_pyevm(mox_path, complex_temp_path, complex_project_config):
    current_dir = Path.cwd()
    try:
        os.chdir(complex_temp_path)
        result = subprocess.run(
            [mox_path, "deploy", "price_feed", "--no-install"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Deployed contract price_feed on pyevm to" in result.stderr


# @dev test adapted to the ordering of dependencies
@pytest.mark.parametrize(
    "cli_args, rewrite_dependencies, expected_lib_path, expected_pip_deps, expected_gh_deps, expected_gh_versions",
    [
        # --no-install should skip package installation
        (["price_feed", "--no-install"], [], False, ["snekmate==0.1.0"], [], None),
        # Default behavior - installs dependencies
        (
            ["price_feed"],
            [
                "PatrickAlphaC/test_repo",
                f"{PIP_PACKAGE_NAME}>={VERSION}",
                f"{MOCCASIN_LIB_NAME}==0.3.6",
            ],
            True,
            [f"{PIP_PACKAGE_NAME}>={VERSION}", f"{MOCCASIN_LIB_NAME}==0.3.6"],
            ["PatrickAlphaC/test_repo"],
            {"patrickalphac/test_repo": "0.1.1"},
        ),
        # Change compiled file
        (["price_feed"], [], True, ["snekmate==0.1.0"], [], None),
    ],
)
def test_deploy_price_feed_pyevm_with_flags(
    complex_temp_path,
    complex_cleanup_out_folder,
    complex_cleanup_dependencies_folder,
    mox_path,
    cli_args,
    rewrite_dependencies,
    expected_lib_path,
    expected_pip_deps,
    expected_gh_deps,
    expected_gh_versions,
):
    current_dir = Path.cwd()
    old_moccasin_toml = rewrite_temp_moccasin_toml_dependencies(
        complex_temp_path, rewrite_dependencies
    )

    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        base_args = [mox_path, "deploy"]
        result = subprocess.run(
            base_args + cli_args, check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)

    assert complex_temp_path.joinpath(MOCCASIN_TOML).exists()

    gh_dir_path = complex_temp_path.joinpath(LIB_GH_PATH)
    pip_dir_path = complex_temp_path.joinpath(LIB_PIP_PATH)
    assert gh_dir_path.exists() == expected_lib_path
    assert pip_dir_path.exists() == expected_lib_path

    for dep in expected_pip_deps:
        pip_requirement = Requirement(dep)
        assert pip_dir_path.joinpath(pip_requirement.name).exists() == expected_lib_path
    if expected_gh_deps:
        for dep in expected_gh_deps:
            assert (
                gh_dir_path.joinpath(dep.lower().split("@")[0]).exists()
                == expected_lib_path
            )

    # Verify config state if versions are expected
    project_root: Path = Config.find_project_root(complex_temp_path)
    config = Config(project_root)
    assert config.dependencies == expected_pip_deps + expected_gh_deps

    # Verify gh versions file contents
    if expected_gh_versions:
        github_versions = get_temp_versions_toml_gh(complex_temp_path)
        assert github_versions == expected_gh_versions

    assert "Deployed contract price_feed on pyevm to" in result.stderr

    # Reset toml to the original for next test
    with open(complex_temp_path.joinpath(MOCCASIN_TOML), "wb") as f:
        tomli_w.dump(old_moccasin_toml, f)


# --------------------------------------------------------------
#                           WITH ANVIL
# --------------------------------------------------------------
def test_deploy_price_feed_anvil(mox_path, complex_temp_path, anvil):
    current_dir = Path.cwd()
    try:
        os.chdir(complex_temp_path)
        result = subprocess.run(
            [mox_path, "deploy", "price_feed", "--network", "anvil"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Deployed contract price_feed on anvil to" in result.stderr
