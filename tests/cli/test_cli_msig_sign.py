import json
import os
import shutil
import subprocess


from tests.utils.anvil import ANVIL_URL

# Constants for CLI commands tests
LOCAL_ANVIL_URL = ANVIL_URL.format(8545)
MSIG_TX_BUILD = ["mox", "msig", "tx_build"]
MSIG_TX_SIGN = ["mox", "msig", "tx_sign"]


def _update_verifying_address(json_path, safe_address):
    """Update the verifyingAddress in the SafeTx JSON file.

    :param json_path: Path to the SafeTx JSON file.
    :param safe_address: The Safe address to set as verifyingAddress.
    """
    with open(json_path, "r") as f:
        safe_tx_data = json.load(f)

    # Handle both SafeTx and EIP-712 formats
    if "safeTx" in safe_tx_data:
        if (
            "domain" in safe_tx_data["safeTx"]
            and "verifyingContract" in safe_tx_data["safeTx"]["domain"]
        ):
            safe_tx_data["safeTx"]["domain"]["verifyingContract"] = safe_address
    elif "domain" in safe_tx_data and "verifyingContract" in safe_tx_data["domain"]:
        safe_tx_data["domain"]["verifyingContract"] = safe_address

    # Save the updated JSON back to the file
    with open(json_path, "w") as f:
        json.dump(safe_tx_data, f, indent=2)


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
def test_cli_tx_sign_with_owner_key(moccasin_home_folder, eth_safe_address_anvil):
    """Sign SafeTx with valid owner private key and dynamically set verifyingAddress."""
    json_path = moccasin_home_folder / "safe-tx-sign.json"
    src_json = os.path.join(os.path.dirname(__file__), "../data/msig_data/safe_tx.json")
    shutil.copyfile(src_json, json_path)

    # Dynamically update verifyingAddress in the JSON file
    _update_verifying_address(json_path, eth_safe_address_anvil)

    owner_key = os.environ.get("ETHEREUM_TEST_PRIVATE_KEY")
    sign_input = (
        f"{LOCAL_ANVIL_URL}\n"
        "n\n"  # not MoccasinAccount
        f"{owner_key}\n"
        "y\n"  # confirm account
        "y\n"  # confirm signing
    )
    result = subprocess.run(
        MSIG_TX_SIGN + ["--input-json", str(json_path)],
        input=sign_input,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert "SafeTx signed successfully!" in result.stdout
    os.remove(json_path)


def test_cli_tx_sign_with_non_owner_key(moccasin_home_folder, eth_safe_address_anvil):
    """Sign SafeTx with non-owner private key (should fail)."""
    json_path = moccasin_home_folder / "safe-tx-nonowner.json"
    src_json = os.path.join(os.path.dirname(__file__), "../data/msig_data/safe_tx.json")
    shutil.copyfile(src_json, json_path)

    # Dynamically update verifyingAddress in the JSON file
    _update_verifying_address(json_path, eth_safe_address_anvil)

    non_owner_key = "0x1111111111111111111111111111111111111111111111111111111111111111"
    sign_input = (
        f"{LOCAL_ANVIL_URL}\n"
        "n\n"  # not MoccasinAccount
        f"{non_owner_key}\n"
        "y\n"  # confirm account
        "y\n"  # confirm signing
    )
    result = subprocess.run(
        MSIG_TX_SIGN + ["--input-json", str(json_path)],
        input=sign_input,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert "is not one of the Safe owners" in result.stdout
    os.remove(json_path)


def test_cli_tx_sign_with_invalid_key(moccasin_home_folder, eth_safe_address_anvil):
    """Sign SafeTx with invalid private key (should fail)."""
    json_path = moccasin_home_folder / "safe-tx-invalidkey.json"
    src_json = os.path.join(os.path.dirname(__file__), "../data/msig_data/safe_tx.json")
    shutil.copyfile(src_json, json_path)

    # Dynamically update verifyingAddress in the JSON file
    _update_verifying_address(json_path, eth_safe_address_anvil)

    invalid_key = "0xZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"
    sign_input = (
        f"{LOCAL_ANVIL_URL}\n"
        "n\n"  # not MoccasinAccount
        f"{invalid_key}\n"
        "y\n"  # confirm account
        "y\n"  # confirm signing
    )
    result = subprocess.run(
        MSIG_TX_SIGN + ["--input-json", str(json_path)],
        input=sign_input,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert "invalid" in result.stdout.lower() or "Error initializing" in result.stdout
    os.remove(json_path)


def test_cli_tx_sign_user_abort(moccasin_home_folder, eth_safe_address_anvil):
    """Sign SafeTx but user aborts at confirmation prompt."""
    json_path = moccasin_home_folder / "safe-tx-abort.json"
    src_json = os.path.join(os.path.dirname(__file__), "../data/msig_data/safe_tx.json")
    shutil.copyfile(src_json, json_path)

    # Dynamically update verifyingAddress in the JSON file
    _update_verifying_address(json_path, eth_safe_address_anvil)

    owner_key = os.environ.get("ETHEREUM_TEST_PRIVATE_KEY")
    sign_input = (
        f"{LOCAL_ANVIL_URL}\n"
        "n\n"  # not MoccasinAccount
        f"{owner_key}\n"
        "y\n"  # confirm account
        "n\n"  # abort signing
    )

    result = subprocess.run(
        MSIG_TX_SIGN + ["--input-json", str(json_path)],
        input=sign_input,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert (
        "User aborted" in result.stdout
        or "Aborting signing" in result.stdout
        or result.returncode != 0
    )
    os.remove(json_path)


def test_cli_tx_sign_missing_json(moccasin_home_folder):
    """Sign SafeTx with missing JSON file (should fail)."""
    missing_path = moccasin_home_folder / "does_not_exist.json"
    sign_input = ""
    result = subprocess.run(
        MSIG_TX_SIGN
        + ["--rpc-url", LOCAL_ANVIL_URL, "--input-json", str(missing_path)],
        input=sign_input,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    assert "not found" in result.stdout.lower() or "No such file" in result.stderr
