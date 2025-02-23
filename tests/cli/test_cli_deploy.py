import os
import subprocess
from pathlib import Path

import pytest
import tomli_w

from moccasin.config import Config
from tests.constants import (
    LIB_GH_PATH,
    LIB_PIP_PATH,
    MOCCASIN_TOML,
    NEW_VERSION,
    PATRICK_PACKAGE_NAME,
    PIP_PACKAGE_NAME,
    VERSION,
)
from tests.utils.helpers import (
    get_temp_versions_toml_from_libs,
    rewrite_temp_moccasin_toml_dependencies,
)


# --------------------------------------------------------------
#                         WITHOUT ANVIL
# --------------------------------------------------------------
def test_deploy_price_feed_pyevm(
    mox_path, complex_temp_path, complex_cleanup_out_folder, complex_project_config
):
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


@pytest.mark.parametrize(
    "cli_args, expect_gh_path, expect_pip_path, expect_pip_version, expect_gh_package, dependencies",
    [
        # --no-install should skip package installation
        (["--no-install"], False, False, f"=={VERSION}", False, []),
        # Default behavior - installs dependencies
        ([], False, True, f"=={VERSION}", False, []),
        # --update-packages should update existing dependencies
        (["--update-packages"], True, True, f"=={NEW_VERSION}", True, None),
    ],
)
def test_deploy_default_with_flags(
    complex_temp_path,
    complex_cleanup_dependencies_folder,
    mox_path,
    cli_args,
    expect_gh_path,
    expect_pip_path,
    expect_pip_version,
    expect_gh_package,
    dependencies,
):
    current_dir = Path.cwd()
    if dependencies is not None:
        old_moccasin_toml = rewrite_temp_moccasin_toml_dependencies(
            complex_temp_path, dependencies
        )
    else:
        old_moccasin_toml = rewrite_temp_moccasin_toml_dependencies(complex_temp_path)

    try:
        os.chdir(complex_temp_path)
        base_args = [mox_path, "deploy", "price_feed"]
        result = subprocess.run(
            base_args + cli_args, check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)

    assert complex_temp_path.joinpath(LIB_GH_PATH).exists() == expect_gh_path
    assert complex_temp_path.joinpath(LIB_PIP_PATH).exists() == expect_pip_path

    # Verify config state if versions are expected
    project_root: Path = Config.find_project_root(complex_temp_path)
    config = Config(project_root)
    github_versions, pip_versions = get_temp_versions_toml_from_libs(complex_temp_path)
    assert f"{PIP_PACKAGE_NAME}{expect_pip_version}" in config.dependencies
    if expect_pip_path and expect_pip_version:
        assert pip_versions[f"{PIP_PACKAGE_NAME}"] == expect_pip_version
    if expect_gh_path and expect_gh_package:
        assert PATRICK_PACKAGE_NAME in config.dependencies
        assert github_versions[f"{PATRICK_PACKAGE_NAME}"] == "0.1.1"

    assert "Deployed contract price_feed on pyevm to" in result.stderr

    # Reset toml to the original for next test
    with open(complex_temp_path.joinpath(MOCCASIN_TOML), "wb") as f:
        tomli_w.dump(old_moccasin_toml, f)


# --------------------------------------------------------------
#                           WITH ANVIL
# --------------------------------------------------------------
def test_deploy_price_feed_anvil(
    mox_path, complex_temp_path, complex_cleanup_out_folder, anvil
):
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
