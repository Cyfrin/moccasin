import os
import subprocess
from pathlib import Path

import pytest
import tomli_w
from packaging.requirements import Requirement

from moccasin.config import Config
from tests.constants import (
    ANVIL1_KEYSTORE_NAME,
    ANVIL1_KEYSTORE_PASSWORD,
    ANVIL1_PRIVATE_KEY,
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
def test_run_help(mox_path, complex_temp_path):
    current_dir = Path.cwd()
    try:
        os.chdir(complex_temp_path)
        result = subprocess.run(
            [mox_path, "run", "-h"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "Moccasin CLI run" in result.stdout


def test_run_default(mox_path, complex_temp_path, complex_cleanup_dependencies_folder):
    current_dir = Path.cwd()
    try:
        os.chdir(complex_temp_path)
        result = subprocess.run(
            [mox_path, "run", "deploy"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "Ending count:  1" in result.stdout


# @dev test adapted to the ordering of dependencies
@pytest.mark.parametrize(
    "cli_args, rewrite_dependencies, expected_lib_path, expected_pip_deps, expected_gh_deps, expected_gh_versions",
    [
        # --no-install should skip package installation
        (["deploy", "--no-install"], [], False, ["snekmate==0.1.0"], [], None),
        # Default behavior - installs dependencies
        (
            ["deploy"],
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
        (["deploy"], [], True, ["snekmate==0.1.0"], [], None),
    ],
)
def test_run_default_with_flags(
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
        base_args = [mox_path, "run"]
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

    assert "Ending count:  1" in result.stdout

    # Reset toml to the original for next test
    with open(complex_temp_path.joinpath(MOCCASIN_TOML), "wb") as f:
        tomli_w.dump(old_moccasin_toml, f)


def test_multiple_manifest_returns_the_same_or_different(mox_path, complex_temp_path):
    current_dir = Path.cwd()
    os.chdir(complex_temp_path)
    try:
        result = subprocess.run(
            [mox_path, "run", "quad_manifest"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    print_statements = result.stdout.split("\n")

    # deploymocks vs manifest_named
    assert print_statements[0] != print_statements[1]

    # manifest_named, manifest_named, manifest_named
    assert print_statements[1] == print_statements[2] == print_statements[3]

    # force deploy named
    assert print_statements[4] != print_statements[1] != print_statements[0]

    # deploy mock
    assert (
        print_statements[5]
        != print_statements[1]
        != print_statements[0]
        != print_statements[4]
    )

    assert print_statements[5] != print_statements[4] != print_statements[1]
    assert print_statements[7] == print_statements[4]
    assert print_statements[8] == print_statements[6]
    assert_broadcast_count(print_statements, 0)


# ------------------------------------------------------------------
#                           WITH ANVIL
# ------------------------------------------------------------------
def test_run_with_network(mox_path, complex_temp_path, anvil):
    current_dir = Path.cwd()
    os.chdir(complex_temp_path)
    try:
        result = subprocess.run(
            [
                mox_path,
                "run",
                "deploy",
                "--network",
                "anvil",
                "--private-key",
                ANVIL1_PRIVATE_KEY,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Ending count:  1" in result.stdout
    assert "tx broadcasted" in result.stdout
    assert result.returncode == 0


def test_run_with_keystore_account(mox_path, complex_temp_path, anvil):
    current_dir = Path.cwd()
    os.chdir(complex_temp_path)
    try:
        result = subprocess.run(
            [
                mox_path,
                "run",
                "deploy",
                "--network",
                "anvil",
                "--account",
                ANVIL1_KEYSTORE_NAME,
                "--password",
                ANVIL1_KEYSTORE_PASSWORD,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Ending count:  1" in result.stdout
    assert "tx broadcasted" in result.stdout
    assert result.returncode == 0


def test_run_fork_should_not_send_transactions(
    mox_path,
    complex_temp_path,
    complex_project_config,
    set_fake_chain_rpc,
    anvil_two_no_state,
    anvil_keystore,
):
    current_dir = Path.cwd()
    os.chdir(complex_temp_path)
    try:
        result = subprocess.run(
            [mox_path, "run", "deploy", "--fork", "--network", "anvil-fork"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Ending count:  1" in result.stdout
    assert "tx broadcasted" not in result.stdout
    assert result.returncode == 0


def test_multiple_manifest_returns_the_same_or_different_on_real_network(
    mox_path, complex_temp_path, anvil
):
    current_dir = Path.cwd()
    os.chdir(complex_temp_path)
    try:
        result = subprocess.run(
            [mox_path, "run", "quad_manifest", "--network", "anvil"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    print_statements = result.stdout.split("\n")
    # deploymocks vs manifest_named
    mock_deploy = print_statements[3]
    named_price_feed = print_statements[4]
    named_price_feed_2 = print_statements[5]
    named_price_feed_3 = print_statements[6]
    redeploy_price_feed = print_statements[10]
    mock_deploy_2 = print_statements[14]
    other_price_feed = print_statements[18]
    named_price_feed_5 = print_statements[19]
    other_price_feed_2 = print_statements[20]

    assert mock_deploy != named_price_feed
    assert named_price_feed == named_price_feed_2 == named_price_feed_3
    assert redeploy_price_feed != named_price_feed != mock_deploy
    assert mock_deploy_2 != named_price_feed != mock_deploy
    assert other_price_feed != mock_deploy_2 != named_price_feed != redeploy_price_feed
    assert named_price_feed_5 == named_price_feed
    assert other_price_feed == other_price_feed_2
    assert_broadcast_count(print_statements, 4)


def test_network_should_prompt_on_live(
    mox_path, complex_temp_path, set_fake_chain_rpc, anvil
):
    current_dir = Path.cwd()
    os.chdir(complex_temp_path)
    try:
        result = subprocess.run(
            [mox_path, "run", "deploy", "--network", "anvil-live"],
            input="y\n",
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Ending count:  1" in result.stdout
    assert "tx broadcasted" in result.stdout
    assert "Are you sure you wish to continue?" in result.stdout
    assert result.returncode == 0


def test_network_operation_cancelled_on_no_input(
    mox_path, complex_temp_path, set_fake_chain_rpc, anvil
):
    current_dir = Path.cwd()
    os.chdir(complex_temp_path)
    try:
        result = subprocess.run(
            [mox_path, "run", "deploy", "--network", "anvil-live"],
            input="\n",
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Are you sure you wish to continue?" in result.stdout
    assert "Operation cancelled." in result.stderr
    assert result.returncode == 0


def test_prompt_live_on_non_test_networks(
    mox_path, complex_temp_path, complex_project_config, anvil
):
    current_dir = Path.cwd()
    try:
        os.chdir(complex_temp_path)
        result = subprocess.run(
            [mox_path, "run", "deploy", "--network", "anvil-live"],
            input="\n",
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert (
        "The transactions run on this will actually be broadcast/transmitted, spending gas associated with your account. Are you sure you wish to continue?"
        in result.stdout
    )


# ------------------------------------------------------------------
#                            HELPERS
# ------------------------------------------------------------------
def assert_broadcast_count(print_statements: list, count: int):
    broadcast_count = 0
    for statement in print_statements:
        if "tx broadcasted" in statement:
            broadcast_count += 1
    assert broadcast_count == count
