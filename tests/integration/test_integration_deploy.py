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
    PACKAGE_VERSION,
    PIP_PACKAGE_NAME,
)
from tests.utils.helpers import (
    get_temp_versions_toml_gh,
    rewrite_temp_moccasin_toml_dependencies,
)


# @dev test adapted to the ordering of dependencies
@pytest.mark.parametrize(
    "cli_args, rewrite_dependencies, expected_lib_path, expected_pip_deps, expected_gh_deps, expected_gh_versions",
    [
        # --no-install should skip package installation
        (["price_feed", "--no-install"], [], False, [], [], None),
        # Default behavior - installs dependencies
        (
            ["price_feed"],
            [
                "PatrickAlphaC/test_repo",
                f"{PIP_PACKAGE_NAME}>={PACKAGE_VERSION}",
                f"{MOCCASIN_LIB_NAME}==0.3.6",
            ],
            True,
            [f"{PIP_PACKAGE_NAME}>={PACKAGE_VERSION}", f"{MOCCASIN_LIB_NAME}==0.3.6"],
            ["PatrickAlphaC/test_repo"],
            {"patrickalphac/test_repo": "0.1.2"},
        ),
        # Change compiled file
        (["price_feed"], [], True, ["snekmate==0.1.1"], [], None),
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

    if "--no-install" not in cli_args:
        assert gh_dir_path.exists()
        assert pip_dir_path.exists()

    for dep in expected_pip_deps:
        pip_requirement = Requirement(dep)
        assert pip_dir_path.joinpath(pip_requirement.name).exists()
    if expected_gh_deps:
        for dep in expected_gh_deps:
            assert gh_dir_path.joinpath(dep.lower().split("@")[0]).exists()

    # Verify config state if versions are expected
    project_root: Path = Config.find_project_root(complex_temp_path)
    config = Config(project_root)
    if "--no-install" not in cli_args:
        assert config.dependencies == expected_pip_deps + expected_gh_deps

    # Verify gh versions file contents
    if expected_gh_versions:
        github_versions = get_temp_versions_toml_gh(complex_temp_path)
        assert github_versions == expected_gh_versions

    assert "Deployed contract price_feed on pyevm to" in result.stderr

    # Reset toml to the original for next test
    with open(complex_temp_path.joinpath(MOCCASIN_TOML), "wb") as f:
        tomli_w.dump(old_moccasin_toml, f)
