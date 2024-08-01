from pathlib import Path
import subprocess
import os
from tests.utils.anvil import AnvilProcess
from tests.cli.conftest import (
    COMPLEX_PROJECT_PATH,
    ANVIL1_PRIVATE_KEY,
    ANVIL1_KEYSTORE_NAME,
    ANVIL1_KEYSTORE_PASSWORD,
)


def test_run_help(gab_path):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [gab_path, "run", "-h"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Gaboon CLI run" in result.stdout


def test_run_default(gab_path):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [gab_path, "run", "deploy"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Ending count:  1" in result.stdout


def test_run_with_network(gab_path):
    current_dir = Path.cwd()
    os.chdir(COMPLEX_PROJECT_PATH)
    try:
        with AnvilProcess():
            result = subprocess.run(
                [
                    gab_path,
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


def test_run_with_keystore_account(gab_path, anvil_keystore):
    current_dir = Path.cwd()
    os.chdir(COMPLEX_PROJECT_PATH)
    try:
        with AnvilProcess():
            result = subprocess.run(
                [
                    gab_path,
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
