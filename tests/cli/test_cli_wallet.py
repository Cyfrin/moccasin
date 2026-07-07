import os
import subprocess
from pathlib import Path

import pytest

import moccasin.constants.vars as vars
from moccasin.constants.vars import MOCCASIN_KEYSTORES_FOLDER_NAME
from tests.constants import COMPLEX_PROJECT_PATH


def test_run_help(mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "wallet", "-h"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "Moccasin CLI wallet" in result.stdout


def test_run_keystore_location(mox_path, moccasin_home_folder):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "wallet", "keystore-location"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    # @dev using moccasin_home_folder fixture due to MOCCASIN_KEYSTORE_PATH
    # being modified during session tests in temporary directory
    assert (
        f"Keystore location: {moccasin_home_folder.joinpath(MOCCASIN_KEYSTORES_FOLDER_NAME)} (default location)"
        in result.stderr
    )


def test_run_keystore_location_custom(mox_path, custom_moccasin_keystore_path):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "wallet", "keystore-location"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert (
        f"Keystore location: {str(custom_moccasin_keystore_path)} (custom location)"
        in result.stderr
    )


def test_run_keystore_location_alias(
    mox_path, moccasin_home_folder, session_monkeypatch
):
    default_keystore = moccasin_home_folder.joinpath(MOCCASIN_KEYSTORES_FOLDER_NAME)
    session_monkeypatch.setenv("MOCCASIN_KEYSTORE_PATH", str(default_keystore))
    session_monkeypatch.setattr(vars, "MOCCASIN_KEYSTORE_PATH", default_keystore)

    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "wallet", "kl"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    output = result.stderr + result.stdout
    assert (
        f"Keystore location: {default_keystore} (default location)" in output
    )
    assert "Unknown accounts command" not in output


def test_run_wallet_list_alias(mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "wallet", "ls"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Unknown accounts command" not in result.stderr


@pytest.mark.parametrize("wallet_alias", ["g", "new"])
def test_run_wallet_generate_aliases(mox_path, wallet_alias):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "wallet", wallet_alias, "test-alias-account"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Account generated:" in result.stderr
    assert "Unknown accounts command" not in result.stderr


def test_run_wallet_delete_alias_for_missing_account(mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "wallet", "d", "missing-alias-account"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Account with name missing-alias-account does not exist" in result.stderr
    assert "Unknown accounts command" not in result.stderr


@pytest.mark.parametrize(
    ("wallet_alias", "canonical_command"),
    [
        ("ls", "list"),
        ("g", "generate"),
        ("new", "generate"),
        ("i", "import"),
        ("add", "import"),
        ("dk", "decrypt"),
        ("d", "delete"),
    ],
)
def test_wallet_alias_help(mox_path, wallet_alias, canonical_command):
    result = subprocess.run(
        [mox_path, "wallet", wallet_alias, "-h"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert f"wallet {canonical_command}" in result.stdout
