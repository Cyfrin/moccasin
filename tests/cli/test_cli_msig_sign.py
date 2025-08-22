import os
import subprocess
from pathlib import Path

from tests.constants import ANVIL1_KEYSTORE_NAME, ANVIL1_KEYSTORE_PASSWORD
from tests.utils.anvil import ANVIL_URL

# Constants for CLI commands tests
LOCAL_ANVIL_URL = ANVIL_URL.format(8545)


################################################################
#                  SAFE INSTANCE ANVIL TEST                     #
################################################################
def test_eth_safe_address_anvil_fixture(eth_safe_address_anvil):
    """Sanity check: eth_safe_address_anvil fixture returns a valid Safe instance and contract address."""
    # Address should be a non-empty string and start with 0x
    assert isinstance(eth_safe_address_anvil, str)
    assert eth_safe_address_anvil.startswith("0x")
    # 20 bytes + 0x prefix
    assert len(eth_safe_address_anvil) == 42


################################################################
#                        TX_SIGN TESTS                         #
################################################################
def test_cli_tx_sign_with_owner_key(
    mox_path, moccasin_home_folder, safe_tx_input_json, owner_key
):
    """Sign SafeTx with valid owner private key and dynamically set verifyingAddress."""
    sign_input = (
        f"{LOCAL_ANVIL_URL}\n"
        "n\n"  # not MoccasinAccount
        f"{owner_key}\n"
        "y\n"  # confirm account
        "y\n"  # confirm signing
    )

    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        result = subprocess.run(
            [mox_path, "msig", "tx-sign", "--input-json", str(safe_tx_input_json)],
            input=sign_input,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)

    assert "SafeTx signed successfully!" in result.stdout


def test_cli_tx_sign_with_non_owner_key(
    mox_path, moccasin_home_folder, safe_tx_input_json
):
    """Sign SafeTx with non-owner private key (should fail)."""
    non_owner_key = "0x1111111111111111111111111111111111111111111111111111111111111111"
    sign_input = (
        f"{LOCAL_ANVIL_URL}\n"
        "n\n"  # not MoccasinAccount
        f"{non_owner_key}\n"
        "y\n"  # confirm account
        "y\n"  # confirm signing
    )

    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        result = subprocess.run(
            [mox_path, "msig", "tx-sign", "--input-json", str(safe_tx_input_json)],
            input=sign_input,
            text=True,
            capture_output=True,
            # check=True,  # Removed to allow assertion on result content
            timeout=30,
        )
    finally:
        os.chdir(current_dir)

    assert (
        "is not one of the Safe owners. Cannot proceed with signing." in result.stderr
    )


def test_cli_tx_sign_with_invalid_key(
    mox_path, moccasin_home_folder, safe_tx_input_json
):
    """Sign SafeTx with invalid private key (should fail)."""
    invalid_key = "0xZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"
    sign_input = (
        f"{LOCAL_ANVIL_URL}\n"
        "n\n"  # not MoccasinAccount
        f"{invalid_key}\n"
        "y\n"  # confirm account
        "y\n"  # confirm signing
    )

    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        result = subprocess.run(
            [mox_path, "msig", "tx-sign", "--input-json", str(safe_tx_input_json)],
            input=sign_input,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)

    assert "invalid" in result.stdout.lower() or "Error initializing" in result.stdout


def test_cli_tx_sign_user_abort(
    mox_path, moccasin_home_folder, safe_tx_input_json, owner_key
):
    """Sign SafeTx but user aborts at confirmation prompt."""
    sign_input = (
        f"{LOCAL_ANVIL_URL}\n"
        "n\n"  # not MoccasinAccount
        f"{owner_key}\n"
        "y\n"  # confirm account
        "n\n"  # abort signing
    )

    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        result = subprocess.run(
            [mox_path, "msig", "tx-sign", "--input-json", str(safe_tx_input_json)],
            input=sign_input,
            text=True,
            capture_output=True,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)

    assert "User aborted tx_sign command." in result.stderr


def test_cli_tx_sign_missing_json(mox_path, moccasin_home_folder, safe_tx_input_json):
    """Sign SafeTx with missing JSON file (should fail)."""
    missing_path = moccasin_home_folder / "does_not_exist.json"
    sign_input = ""
    result = subprocess.run(
        [
            mox_path,
            "msig",
            "tx-sign",
            "--rpc",
            LOCAL_ANVIL_URL,
            "--input-json",
            str(missing_path),
        ],
        input=sign_input,
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert "No such file or directory:" in result.stderr


def test_cli_tx_sign_with_moccasin_keystore(
    mox_path, moccasin_home_folder, safe_tx_input_json
):
    """Sign SafeTx using Moccasin keystore account and correct password."""
    sign_input = (
        f"{LOCAL_ANVIL_URL}\n"
        "y\n"  # Use Moccasin account
        f"{ANVIL1_KEYSTORE_NAME}\n"
        f"{ANVIL1_KEYSTORE_PASSWORD}\n"
        "y\n"  # confirm account
        "y\n"  # confirm signing
    )

    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        result = subprocess.run(
            [mox_path, "msig", "tx-sign", "--input-json", str(safe_tx_input_json)],
            input=sign_input,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)

    assert "SafeTx signed successfully!" in result.stdout


def test_cli_tx_sign_with_keystore_wrong_password(
    mox_path, moccasin_home_folder, safe_tx_input_json
):
    """Sign SafeTx using Moccasin keystore account and wrong password (should fail)."""
    wrong_password = "not_the_right_password"
    sign_input = (
        f"{LOCAL_ANVIL_URL}\n"
        "y\n"  # Use Moccasin account
        f"{ANVIL1_KEYSTORE_NAME}\n"
        f"{wrong_password}\n"
        "y\n"  # confirm account
        "y\n"  # confirm signing
    )

    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        result = subprocess.run(
            [mox_path, "msig", "tx-sign", "--input-json", str(safe_tx_input_json)],
            input=sign_input,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)

    assert "ValueError: Passwords do not match" in result.stderr


def test_cli_tx_sign_with_nonexistent_keystore(
    mox_path, moccasin_home_folder, safe_tx_input_json
):
    """Sign SafeTx using a non-existent Moccasin keystore (should fail)."""
    fake_keystore_name = "does_not_exist"
    sign_input = (
        f"{LOCAL_ANVIL_URL}\n"
        "y\n"  # Use Moccasin account
        f"{fake_keystore_name}\n"
        "anypassword\n"
        "y\n"  # confirm account
        "y\n"  # confirm signing
    )

    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        result = subprocess.run(
            [mox_path, "msig", "tx-sign", "--input-json", str(safe_tx_input_json)],
            input=sign_input,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)

    assert "No such file or directory" in result.stderr
    assert "does_not_exist" in result.stderr


def test_cli_tx_sign_interactive_input_json_prompt(
    mox_path, moccasin_home_folder, safe_tx_input_json
):
    """Test interactive fallback: CLI prompts for input JSON when --input-json is omitted."""
    sign_input = (
        f"{LOCAL_ANVIL_URL}\n"
        f"{safe_tx_input_json}\n"  # Prompted for input JSON file path
        "n\n"  # not MoccasinAccount
        "0x1111111111111111111111111111111111111111111111111111111111111111\n"
        "y\n"  # confirm account
        "y\n"  # confirm signing
    )

    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        result = subprocess.run(
            [mox_path, "msig", "tx-sign"],
            input=sign_input,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)

    # Should fail because key is not owner, but the prompt for input file should work
    assert "is not one of the Safe owners" in result.stderr or "SafeTx" in result.stdout


def test_cli_tx_sign_interactive_output_json_prompt(
    mox_path, moccasin_home_folder, safe_tx_input_json, owner_key
):
    """Test interactive fallback: CLI prompts for output JSON when output file is omitted."""
    output_json_path = moccasin_home_folder / "signed-output.json"
    sign_input = (
        f"{LOCAL_ANVIL_URL}\n"
        "n\n"  # not MoccasinAccount
        f"{owner_key}\n"
        "y\n"  # confirm account
        "y\n"  # confirm signing
        "y\n"  # confirm saving signed SafeTx
        f"{output_json_path}\n"  # Prompted for output file path
    )

    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        result = subprocess.run(
            [mox_path, "msig", "tx-sign", "--input-json", str(safe_tx_input_json)],
            input=sign_input,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)

    assert "SafeTx signed successfully!" in result.stdout
    assert output_json_path.exists()
    os.remove(output_json_path)


"""
@TODO Other tests for tx_sign command:
Multiple Signers
- Test signing the same SafeTx with two different owner accounts (should accumulate signatures).
- Test attempting to sign twice with the same account (should fail with "already signed").

User Prompts and Aborts
- Test user aborts at the "sign with Moccasin account?" prompt.
- Test user aborts at the "confirm account" prompt.
- Test user aborts at the "confirm signing" prompt (already covered).

Output File Handling
- Test signing with a valid output file path (JSON is saved).
- Test signing with an invalid output file path (should fail).
- Test signing with no output file (should prompt and handle gracefully).

SafeTx JSON Variants
- Test signing with a SafeTx JSON missing required fields (should fail).
- Test signing with a SafeTx JSON with extra/unexpected fields (should succeed if core fields are present)
"""
