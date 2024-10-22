import os
import subprocess
from pathlib import Path

from tests.conftest import (
    ANVIL1_KEYSTORE_NAME,
    ANVIL1_KEYSTORE_PASSWORD,
    ANVIL1_PRIVATE_KEY,
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


def test_run_default(mox_path, complex_temp_path):
    current_dir = Path.cwd()
    try:
        os.chdir(complex_temp_path)
        result = subprocess.run(
            [mox_path, "run", "deploy"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "Ending count:  1" in result.stdout


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
