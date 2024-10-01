import os
import subprocess
from pathlib import Path

from tests.conftest import (
    ANVIL1_KEYSTORE_NAME,
    ANVIL1_KEYSTORE_PASSWORD,
    ANVIL1_PRIVATE_KEY,
    COMPLEX_PROJECT_PATH,
)


# --------------------------------------------------------------
#                         WITHOUT ANVIL
# --------------------------------------------------------------
def test_run_help(mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "run", "-h"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "Moccasin CLI run" in result.stdout


def test_run_default(mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "run", "deploy"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "Ending count:  1" in result.stdout


def test_multiple_manifest_returns_the_same_or_different(mox_path):
    current_dir = Path.cwd()
    os.chdir(COMPLEX_PROJECT_PATH)
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
    assert print_statements[0] == print_statements[1] == print_statements[2]
    assert print_statements[3] != print_statements[0]
    assert_broadcast_count(print_statements, 0)


# ------------------------------------------------------------------
#                           WITH ANVIL
# ------------------------------------------------------------------
def test_run_with_network(mox_path, anvil_process):
    current_dir = Path.cwd()
    os.chdir(COMPLEX_PROJECT_PATH)
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


def test_run_with_keystore_account(mox_path, anvil_keystore, anvil_process):
    current_dir = Path.cwd()
    os.chdir(COMPLEX_PROJECT_PATH)
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
    mox_path, complex_project_config, set_fake_chain_rpc, anvil_fork_no_state
):
    current_dir = Path.cwd()
    os.chdir(COMPLEX_PROJECT_PATH)
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
    mox_path, anvil_process
):
    current_dir = Path.cwd()
    os.chdir(COMPLEX_PROJECT_PATH)
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
    assert print_statements[0] == print_statements[1] == print_statements[2]
    assert print_statements[3] != print_statements[0]
    assert_broadcast_count(print_statements, 1)


def test_network_should_prompt_on_live(mox_path, set_fake_chain_rpc, anvil_process):
    current_dir = Path.cwd()
    os.chdir(COMPLEX_PROJECT_PATH)
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
    mox_path, set_fake_chain_rpc, anvil_process
):
    current_dir = Path.cwd()
    os.chdir(COMPLEX_PROJECT_PATH)
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
    mox_path, complex_project_config, anvil_process
):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
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
