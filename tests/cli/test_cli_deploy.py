import os
import subprocess
from pathlib import Path

import tomli_w

from moccasin.config import Config
from tests.constants import (
    LIB_GH_PATH,
    LIB_PIP_PATH,
    MOCCASIN_TOML,
    NEW_VERSION,
    PATRICK_PACKAGE_NAME,
    PIP_PACKAGE_NAME,
)
from tests.utils.helpers import (
    get_temp_versions_toml_from_libs,
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
            [mox_path, "deploy", "price_feed"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Deployed contract price_feed on pyevm to" in result.stderr


def test_deploy_price_feed_pyevm_and_update(
    mox_path, complex_temp_path, complex_project_config
):
    current_dir = Path.cwd()
    try:
        os.chdir(complex_temp_path)
        result = subprocess.run(
            [mox_path, "deploy", "price_feed"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Deployed contract price_feed on pyevm to" in result.stderr

    # Second run should update the version in the config
    old_moccasin_toml = rewrite_temp_moccasin_toml_dependencies(complex_temp_path)

    try:
        os.chdir(complex_temp_path)
        result_two = subprocess.run(
            [mox_path, "deploy", "price_feed", "--update-packages"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)

    assert complex_temp_path.joinpath(LIB_PIP_PATH).exists()
    assert complex_temp_path.joinpath(LIB_GH_PATH).exists()

    project_root: Path = Config.find_project_root(complex_temp_path)
    config = Config(project_root)
    assert f"{PIP_PACKAGE_NAME}=={NEW_VERSION}" in config.dependencies
    assert f"{PATRICK_PACKAGE_NAME}" in config.dependencies

    github_versions, pip_versions = get_temp_versions_toml_from_libs(complex_temp_path)
    assert github_versions[f"{PATRICK_PACKAGE_NAME}"] == "0.1.1"
    assert pip_versions[f"{PIP_PACKAGE_NAME}"] == f"=={NEW_VERSION}"

    # Check for the error message in the output
    assert "Deployed contract price_feed on pyevm to" in result_two.stderr

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
