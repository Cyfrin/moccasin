import os
import subprocess
from pathlib import Path

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
#                       TX_MSIG WORKFLOW                       #
################################################################
def test_cli_full_workflow_success(
    mox_path, moccasin_home_folder, eth_safe_address_anvil, owner_key, owner2_key
):
    """Full workflow: build, sign, broadcast SafeTx (all prompts, success)."""
    json_path = moccasin_home_folder / "safe-tx-workflow.json"
    # Build SafeTx
    build_input = (
        f"{LOCAL_ANVIL_URL}\n"
        f"{eth_safe_address_anvil}\n"
        "0\n"
        "0x0000000000000000000000000000000000000000\n"
        "0x0000000000000000000000000000000000000000\n"
        "1\n"
        "0\n"
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48\n"
        "10\n"
        "0\n"
        "transfer(address,uint256)\n"
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266\n"
        "100\n"
        "y\n"
        f"{json_path}\n"
    )
    if json_path.exists():
        os.remove(json_path)
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        build_result = subprocess.run(
            [mox_path, "msig", "tx-build"],
            input=build_input,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)
    assert "SafeTx instance created successfully!" in build_result.stdout
    assert json_path.exists()

    # Sign SafeTx with two owners (threshold=2)
    # Prepare sign inputs for both owners
    sign_input1 = f"{LOCAL_ANVIL_URL}\nn\n{owner_key}\ny\ny\ny\n{json_path}\n"
    sign_input2 = f"{LOCAL_ANVIL_URL}\nn\n{owner2_key}\ny\ny\n"
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        sign_result1 = subprocess.run(
            [mox_path, "msig", "tx-sign", "--input-json", str(json_path)],
            input=sign_input1,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
        sign_result2 = subprocess.run(
            [
                mox_path,
                "msig",
                "tx-sign",
                "--input-json",
                str(json_path),
                "--output-json",
                str(json_path),
            ],
            input=sign_input2,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)
    assert "SafeTx signed successfully!" in sign_result1.stdout
    assert "SafeTx signed successfully!" in sign_result2.stdout

    # Broadcast SafeTx
    broadcast_input = f"{LOCAL_ANVIL_URL}\nn\n{owner_key}\ny\ny\n"
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        broadcast_result = subprocess.run(
            [
                mox_path,
                "msig",
                "tx-broadcast",
                "--input-json",
                str(json_path),
                "--output-json",
                str(json_path),
            ],
            input=broadcast_input,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)
    assert "SafeTx broadcasted successfully!" in broadcast_result.stdout
    os.remove(json_path)


def test_cli_broadcast_missing_signatures(
    mox_path, moccasin_home_folder, eth_safe_address_anvil, owner_key
):
    """Broadcast SafeTx with missing signatures (should fail)."""
    json_path = moccasin_home_folder / "safe-tx-missing-sig.json"
    # Build SafeTx
    build_input = (
        f"{LOCAL_ANVIL_URL}\n"
        f"{eth_safe_address_anvil}\n"
        "0\n"
        "0x0000000000000000000000000000000000000000\n"
        "0x0000000000000000000000000000000000000000\n"
        "1\n"
        "0\n"
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48\n"
        "10\n"
        "0\n"
        "transfer(address,uint256)\n"
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266\n"
        "100\n"
        "y\n"
        f"{json_path}\n"
    )
    if json_path.exists():
        os.remove(json_path)
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        build_result = subprocess.run(
            [mox_path, "msig", "tx-build"],
            input=build_input,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)
    assert "SafeTx instance created successfully!" in build_result.stdout
    assert json_path.exists()

    # Sign SafeTx with only one owner (threshold=2), prompt for output file
    sign_input = f"{LOCAL_ANVIL_URL}\nn\n{owner_key}\ny\ny\ny\n{json_path}\n"
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        sign_result = subprocess.run(
            [mox_path, "msig", "tx-sign", "--input-json", str(json_path)],
            input=sign_input,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)
    assert "SafeTx signed successfully!" in sign_result.stdout

    # Try to broadcast (should fail)
    broadcast_input = f"{LOCAL_ANVIL_URL}\nn\n{owner_key}\ny\ny\n"
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        broadcast_result = subprocess.run(
            [
                mox_path,
                "msig",
                "tx-broadcast",
                "--input-json",
                str(json_path),
                "--output-json",
                str(json_path),
            ],
            input=broadcast_input,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)
    assert (
        "requires at least" in broadcast_result.stderr
        or "signers" in broadcast_result.stderr
    )
    os.remove(json_path)


def test_cli_broadcast_non_owner_signature(
    mox_path, moccasin_home_folder, eth_safe_address_anvil
):
    """Broadcast SafeTx signed by non-owner (should fail)."""
    json_path = moccasin_home_folder / "safe-tx-non-owner.json"
    non_owner_key = "0x1111111111111111111111111111111111111111111111111111111111111111"
    # Build SafeTx
    build_input = (
        f"{LOCAL_ANVIL_URL}\n"
        f"{eth_safe_address_anvil}\n"
        "0\n"
        "0x0000000000000000000000000000000000000000\n"
        "0x0000000000000000000000000000000000000000\n"
        "1\n"
        "0\n"
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48\n"
        "10\n"
        "0\n"
        "transfer(address,uint256)\n"
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266\n"
        "100\n"
        "y\n"
        f"{json_path}\n"
    )
    if json_path.exists():
        os.remove(json_path)
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        build_result = subprocess.run(
            [mox_path, "msig", "tx-build"],
            input=build_input,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)
    assert "SafeTx instance created successfully!" in build_result.stdout
    assert json_path.exists()

    # Sign SafeTx with non-owner key, prompt for output file
    sign_input = f"{LOCAL_ANVIL_URL}\nn\n{non_owner_key}\ny\ny\ny\n{json_path}\n"
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        sign_result = subprocess.run(
            [mox_path, "msig", "tx-sign", "--input-json", str(json_path)],
            input=sign_input,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)
    assert "is not one of the Safe owners" in sign_result.stderr

    # Try to broadcast
    broadcast_input = f"{LOCAL_ANVIL_URL}\nn\n{non_owner_key}\ny\ny\n"
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        broadcast_result = subprocess.run(
            [
                mox_path,
                "msig",
                "tx-broadcast",
                "--input-json",
                str(json_path),
                "--output-json",
                str(json_path),
            ],
            input=broadcast_input,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)
    assert (
        "requires at least" in broadcast_result.stderr
        or "signers" in broadcast_result.stderr
    )
    os.remove(json_path)


def test_cli_broadcast_user_abort(
    mox_path, moccasin_home_folder, eth_safe_address_anvil, owner_key, owner2_key
):
    """User aborts at broadcast confirmation prompt (should fail)."""
    json_path = moccasin_home_folder / "safe-tx-abort.json"
    owner_key = os.environ.get("ETHEREUM_TEST_PRIVATE_KEY")
    # Build SafeTx
    build_input = (
        f"{LOCAL_ANVIL_URL}\n"
        f"{eth_safe_address_anvil}\n"
        "0\n"
        "0x0000000000000000000000000000000000000000\n"
        "0x0000000000000000000000000000000000000000\n"
        "1\n"
        "0\n"
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48\n"
        "10\n"
        "0\n"
        "transfer(address,uint256)\n"
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266\n"
        "100\n"
        "y\n"
        f"{json_path}\n"
    )
    if json_path.exists():
        os.remove(json_path)
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        build_result = subprocess.run(
            [mox_path, "msig", "tx-build"],
            input=build_input,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)
    assert "SafeTx instance created successfully!" in build_result.stdout
    assert json_path.exists()

    # Sign SafeTx with two owners (threshold=2), prompt for output file
    sign_input1 = f"{LOCAL_ANVIL_URL}\nn\n{owner_key}\ny\ny\ny\n{json_path}\n"
    sign_input2 = f"{LOCAL_ANVIL_URL}\nn\n{owner2_key}\ny\ny\ny\n{json_path}\n"
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        sign_result1 = subprocess.run(
            [mox_path, "msig", "tx-sign", "--input-json", str(json_path)],
            input=sign_input1,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
        sign_result2 = subprocess.run(
            [mox_path, "msig", "tx-sign", "--input-json", str(json_path)],
            input=sign_input2,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)
    assert "SafeTx signed successfully!" in sign_result1.stdout
    assert "SafeTx signed successfully!" in sign_result2.stdout

    # Broadcast SafeTx, but abort at confirmation
    broadcast_input = f"{LOCAL_ANVIL_URL}\nn\n{owner_key}\ny\nn\n"
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        broadcast_result = subprocess.run(
            [
                mox_path,
                "msig",
                "tx-broadcast",
                "--input-json",
                str(json_path),
                "--output-json",
                str(json_path),
            ],
            input=broadcast_input,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    finally:
        os.chdir(current_dir)
    assert "User aborted tx_broadcast command." in broadcast_result.stderr
    os.remove(json_path)
