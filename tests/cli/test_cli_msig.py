import json
import os
import subprocess
import pytest

from tests.utils.anvil import ANVIL_URL

# Constants for CLI commands tests
LOCAL_ANVIL_URL = ANVIL_URL.format(8545)
MSIG_TX_BUILD = ["mox", "msig", "tx_build"]
MSIG_TX_SIGN = ["mox", "msig", "tx_sign"]


################################################################
#                  SAFE INSTANCE ANVIL TEST                     #
################################################################
def test_eth_safe_address_anvil_fixture(eth_safe_address_anvil):
    """Sanity check: eth_safe_address_anvil fixture returns a valid Safe instance and contract address."""
    # Should be a Safe instance
    assert hasattr(eth_safe_address_anvil, "contract_address"), (
        "Fixture did not return a Safe instance with address"
    )
    # Address should be a non-empty string and start with 0x
    assert isinstance(eth_safe_address_anvil, str)
    assert eth_safe_address_anvil.startswith("0x")
    # 20 bytes + 0x prefix
    assert len(eth_safe_address_anvil) == 42


################################################################
#                        TX_BUILD TESTS                        #
################################################################
def test_cli_tx_builder_interactive(temp_msig_workdir, eth_safe_address_anvil):
    """Test fully interactive session (all prompts, user saves JSON)."""
    json_path = temp_msig_workdir / "safe-tx.json"
    user_input = (
        # RPC URL (question: What is the RPC URL you want to use to connect to the Ethereum network?)
        f"{LOCAL_ANVIL_URL}\n"
        # Safe address (question: What is the address of the Safe contract you want to use?)
        f"{eth_safe_address_anvil}\n"
        # Safe nonce (question: What nonce should be used for this Safe transaction?)
        "42\n"
        # Gas token (question: What is the gas token address to use for this transaction? (Press Enter to use the default/zero address))
        "0x0000000000000000000000000000000000000000\n"
        # Number of internal txs (question: How many internal transactions would you like to include in this batch?)
        "1\n"
        # Internal tx type (question: What type of internal transaction is this? (0 = call contract, 1 = ERC20 transfer, 2 = raw data))
        "0\n"
        # Contract address (question: What is the contract address for this call?)
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48\n"
        # Value in wei (question: How much value (in wei) should be sent with this call?)
        "10\n"
        # Operation type (question: What operation type should be used? (0 = call, 1 = delegate call))
        "0\n"
        # Function signature (question: What is the function signature for this call? (e.g. transfer(address,uint256)))
        "transfer(address,uint256)\n"
        # Param 1 (question: What value should be used for parameter #1 of type address?)
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266\n"
        # Param 2 (question: What value should be used for parameter #2 of type uint256?)
        "100\n"
        # Save EIP-712 JSON? (question: Would you like to save the EIP-712 structured data to a .json file? (y/n))
        "y\n"
        # File path (question: Where would you like to save the EIP-712 JSON file? (e.g. ./safe-tx.json))
        "safe-tx.json\n"
        # After saving, CLI will ask if you want to continue to the next step (signer). We answer 'q' to quit.
        "q\n"
    )
    if json_path.exists():
        os.remove(json_path)
    result = subprocess.run(
        MSIG_TX_BUILD,
        input=user_input,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert "SafeTx instance created successfully!" in result.stdout
    assert json_path.exists()
    with open(json_path) as f:
        safe_tx_data = json.load(f)
    assert "types" in safe_tx_data["safeTx"] and "message" in safe_tx_data["safeTx"]
    assert safe_tx_data["safeTx"]["message"]["data"].startswith("0x")
    assert bytes.fromhex(safe_tx_data["signatures"].lstrip("0x")) == b""

    os.remove(json_path)


def test_cli_tx_builder_args_only(temp_msig_workdir, eth_safe_address_anvil):
    """Test all args provided, no prompts, no JSON output."""
    args = [
        "--rpc-url",
        LOCAL_ANVIL_URL,
        "--safe-address",
        eth_safe_address_anvil,
        "--to",
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        "--operation",
        "0",
        "--value",
        "10",
        "--data",
        "0xa9059cbb000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb480000000000000000000000000000000000000000000000000000000000000064",
        "--safe-nonce",
        "42",
        "--gas-token",
        "0x0000000000000000000000000000000000000000",
    ]
    result = subprocess.run(
        MSIG_TX_BUILD + args,
        input="q\n",
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert "SafeTx instance created successfully!" in result.stdout


def test_cli_tx_builder_args_with_json_output(
    temp_msig_workdir, eth_safe_address_anvil
):
    """Test all args provided, with --json-output, file is created and valid."""
    json_path = temp_msig_workdir / "test-tx.json"
    args = [
        "--rpc-url",
        LOCAL_ANVIL_URL,
        "--safe-address",
        eth_safe_address_anvil,
        "--to",
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        "--operation",
        "0",
        "--value",
        "10",
        "--data",
        "0xa9059cbb000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb480000000000000000000000000000000000000000000000000000000000000064",
        "--safe-nonce",
        "42",
        "--gas-token",
        "0x0000000000000000000000000000000000000000",
        "--json-output",
        "test-tx.json",
    ]
    if json_path.exists():
        os.remove(json_path)
    result = subprocess.run(
        MSIG_TX_BUILD + args,
        input="q\n",
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert "SafeTx instance created successfully!" in result.stdout
    assert json_path.exists()
    with open(json_path) as f:
        safe_tx_data = json.load(f)
    assert "types" in safe_tx_data["safeTx"] and "message" in safe_tx_data["safeTx"]
    assert safe_tx_data["safeTx"]["message"]["data"].startswith("0x")
    assert bytes.fromhex(safe_tx_data["signatures"].lstrip("0x")) == b""
    os.remove(json_path)


def test_cli_tx_builder_invalid_json_output(temp_msig_workdir, eth_safe_address_anvil):
    """Test invalid JSON output path (should fail)."""
    args = [
        "--rpc-url",
        LOCAL_ANVIL_URL,
        "--safe-address",
        eth_safe_address_anvil,
        "--to",
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        "--operation",
        "0",
        "--value",
        "10",
        "--data",
        "0xa9059cbb000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb480000000000000000000000000000000000000000000000000000000000000064",
        "--safe-nonce",
        "42",
        "--gas-token",
        "0x0000000000000000000000000000000000000000",
        "--json-output",
        "not_a_json.txt",
    ]

    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run(
            MSIG_TX_BUILD + args,
            input="q\n",
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )


def test_cli_tx_builder_multisend_mixed_operations(
    temp_msig_workdir, eth_safe_address_anvil
):
    """Test MultiSend batch with mixed CALL and DELEGATE_CALL operations.

    This test simulates a batch with two internal txs: one CALL, one DELEGATE_CALL
    We'll use interactive mode to ensure the CLI prompts for each internal tx
    """

    json_path = temp_msig_workdir / "multisend-mixed.json"
    user_input = (
        # RPC URL
        f"{LOCAL_ANVIL_URL}\n"
        # Safe address
        f"{eth_safe_address_anvil}\n"
        # Safe nonce
        "43\n"
        # Gas token
        "0x0000000000000000000000000000000000000000\n"
        # Number of internal txs
        "2\n"
        # Internal tx 1: type CALL
        "0\n"  # type: call contract
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48\n"  # contract address
        "10\n"  # value
        "0\n"  # operation: call
        "transfer(address,uint256)\n"  # function signature
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266\n"  # param 1
        "100\n"  # param 2
        # Internal tx 2: type CALL, but operation DELEGATE_CALL
        "0\n"  # type: call contract
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48\n"  # contract address
        "20\n"  # value
        "1\n"  # operation: delegate call
        "transfer(address,uint256)\n"  # function signature
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266\n"  # param 1
        "200\n"  # param 2
        # Confirm MultiSend batch
        "y\n"
        # Save EIP-712 JSON? (y/n)
        "y\n"
        # File path
        "multisend-mixed.json\n"
        # After saving, quit
        "q\n"
    )
    if json_path.exists():
        os.remove(json_path)
    result = subprocess.run(
        MSIG_TX_BUILD,
        input=user_input,
        text=True,
        capture_output=True,
        check=True,
        timeout=60,
    )
    assert "MultiSend transaction created successfully!" in result.stdout
    assert "SafeTx instance created successfully!" in result.stdout
    assert json_path.exists()
    with open(json_path) as f:
        safe_tx_data = json.load(f)
    assert "types" in safe_tx_data["safeTx"] and "message" in safe_tx_data["safeTx"]
    assert safe_tx_data["safeTx"]["message"]["data"].startswith("0x")
    assert bytes.fromhex(safe_tx_data["signatures"].lstrip("0x")) == b""
    os.remove(json_path)


def test_cli_tx_builder_multisend_user_rejects(
    temp_msig_workdir, eth_safe_address_anvil
):
    """Test user rejects MultiSend batch confirmation (should abort and not create SafeTx)."""
    user_input = (
        # RPC URL
        f"{LOCAL_ANVIL_URL}\n"
        # Safe address
        f"{eth_safe_address_anvil}\n"
        # Safe nonce
        "44\n"
        # Gas token
        "0x0000000000000000000000000000000000000000\n"
        # Number of internal txs
        "2\n"
        # Internal tx 1: type CALL
        "0\n"
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48\n"
        "10\n"
        "0\n"
        "transfer(address,uint256)\n"
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266\n"
        "100\n"
        # Internal tx 2: type CALL, operation DELEGATE_CALL
        "0\n"
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48\n"
        "20\n"
        "1\n"
        "transfer(address,uint256)\n"
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266\n"
        "200\n"
        # Confirm MultiSend batch (user rejects)
        "n\n"
    )
    result = subprocess.run(
        MSIG_TX_BUILD,
        input=user_input,
        text=True,
        capture_output=True,
        check=False,  # Should not raise, but should not create SafeTx
        timeout=60,
    )
    assert "Aborting due to user rejection of decoded batch." in result.stdout
    assert "SafeTx instance created successfully!" not in result.stdout


def test_cli_tx_builder_prompt_fallbacks(temp_msig_workdir, eth_safe_address_anvil):
    """Test prompt fallback when --to and --operation are omitted, CLI prompts for them."""
    json_path = temp_msig_workdir / "prompt-fallback.json"
    args = [
        "--rpc-url",
        f"{LOCAL_ANVIL_URL}",
        "--safe-address",
        eth_safe_address_anvil,
        "--value",
        "10",
        "--data",
        "0xa9059cbb000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb480000000000000000000000000000000000000000000000000000000000000064",
        "--safe-nonce",
        "45",
        "--gas-token",
        "0x0000000000000000000000000000000000000000",
        "--json-output",
        "prompt-fallback.json",
    ]
    # The CLI should prompt for 'to' and 'operation'.
    user_input = (
        # to (target contract address)
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266\n"
        # operation
        "0\n"
        # After, CLI will prompt to save JSON (already provided as arg, so should not prompt)
        # After saving, quit
        "q\n"
    )
    if json_path.exists():
        os.remove(json_path)
    result = subprocess.run(
        MSIG_TX_BUILD + args,
        input=user_input,
        text=True,
        capture_output=True,
        check=True,
        timeout=60,
    )
    assert "SafeTx instance created successfully!" in result.stdout
    assert json_path.exists()
    with open(json_path) as f:
        safe_tx_data = json.load(f)
    assert "types" in safe_tx_data["safeTx"] and "message" in safe_tx_data["safeTx"]
    assert safe_tx_data["safeTx"]["message"]["data"].startswith("0x")
    assert bytes.fromhex(safe_tx_data["signatures"].lstrip("0x")) == b""

    os.remove(json_path)


def test_cli_tx_builder_invalid_data(temp_msig_workdir, eth_safe_address_anvil):
    """Test invalid hex data for --data, should fail gracefully."""
    args = [
        "--rpc-url",
        LOCAL_ANVIL_URL,
        "--safe-address",
        eth_safe_address_anvil,
        "--to",
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        "--operation",
        "0",
        "--value",
        "10",
        "--data",
        "0xINVALIDHEXDATA",
        "--safe-nonce",
        "46",
        "--gas-token",
        "0x0000000000000000000000000000000000000000",
    ]

    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run(
            MSIG_TX_BUILD + args,
            input="q\n",
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )


def test_cli_tx_builder_multisend_large_batch(
    temp_msig_workdir, eth_safe_address_anvil
):
    """Test MultiSend batch with 10 internal transactions (large batch)."""
    json_path = temp_msig_workdir / "multisend-large.json"
    user_input = (
        # RPC URL
        f"{LOCAL_ANVIL_URL}\n"
        # Safe address
        f"{eth_safe_address_anvil}\n"
        # Safe nonce
        "48\n"
        # Gas token
        "0x0000000000000000000000000000000000000000\n"
        # Number of internal txs
        "10\n"
    )
    # For each of the 10 internal txs, append the required answers
    for i in range(10):
        user_input += (
            # Internal tx type (all CALL for simplicity)
            "0\n"
            # Contract address
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48\n"
            # Value in wei (increment for variety)
            f"{10 * (i + 1)}\n"
            # Operation type (alternate between 0 and 1)
            f"{i % 2}\n"
            # Function signature
            "transfer(address,uint256)\n"
            # Param 1 (use a different address for each)
            f"0xf39Fd6e51aad88F6F4ce6aB8827279cffFb922{str(66 + i).zfill(2)}\n"
            # Param 2 (increment for variety)
            f"{100 * (i + 1)}\n"
        )
    user_input += (
        # Confirm MultiSend batch
        "y\n"
        # Save EIP-712 JSON? (y/n)
        "y\n"
        # File path
        "multisend-large.json\n"
        # After saving, quit
        "q\n"
    )
    if json_path.exists():
        os.remove(json_path)
    result = subprocess.run(
        MSIG_TX_BUILD,
        input=user_input,
        text=True,
        capture_output=True,
        check=True,
        timeout=180,
    )
    assert "MultiSend transaction created successfully!" in result.stdout
    assert "SafeTx instance created successfully!" in result.stdout
    assert json_path.exists()
    with open(json_path) as f:
        safe_tx_data = json.load(f)
    assert "types" in safe_tx_data["safeTx"] and "message" in safe_tx_data["safeTx"]
    assert safe_tx_data["safeTx"]["message"]["data"].startswith("0x")
    assert bytes.fromhex(safe_tx_data["signatures"].lstrip("0x")) == b""
    os.remove(json_path)


################################################################
#                        TX_SIGN TESTS                         #
################################################################


def test_cli_tx_sign_with_owner_key(temp_msig_workdir, eth_safe_address_anvil):
    """Sign SafeTx with valid owner private key."""
    json_path = temp_msig_workdir / "safe-tx-sign.json"
    # Build SafeTx JSON first
    user_input = (
        f"{LOCAL_ANVIL_URL}\n"
        f"{eth_safe_address_anvil}\n"
        "42\n"
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
        "safe-tx-sign.json\n"
        "q\n"
    )
    if json_path.exists():
        os.remove(json_path)
    subprocess.run(
        MSIG_TX_BUILD,
        input=user_input,
        text=True,
        capture_output=False,
        check=True,
        timeout=30,
    )
    # Now sign with valid owner private key
    owner_key = os.environ.get("ETHEREUM_TEST_PRIVATE_KEY")
    sign_input = (
        f"{owner_key}\n"  # private key prompt
        "y\n"  # is right account
        "y\n"  # confirm sign
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


def test_cli_tx_sign_with_non_owner_key(temp_msig_workdir, eth_safe_address_anvil):
    """Sign SafeTx with non-owner private key (should fail)."""
    json_path = temp_msig_workdir / "safe-tx-nonowner.json"
    user_input = (
        f"{LOCAL_ANVIL_URL}\n"
        f"{eth_safe_address_anvil}\n"
        "42\n"
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
        "safe-tx-nonowner.json\n"
        "q\n"
    )
    if json_path.exists():
        os.remove(json_path)
    subprocess.run(
        MSIG_TX_BUILD,
        input=user_input,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    # Use a random non-owner key
    non_owner_key = "0x1111111111111111111111111111111111111111111111111111111111111111"
    sign_input = (
        f"{non_owner_key}\n"  # private key prompt
        "y\n"  # is right account
        "y\n"  # confirm sign
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


def test_cli_tx_sign_with_invalid_key(temp_msig_workdir, eth_safe_address_anvil):
    """Sign SafeTx with invalid private key (should fail)."""
    json_path = temp_msig_workdir / "safe-tx-invalidkey.json"
    user_input = (
        f"{LOCAL_ANVIL_URL}\n"
        f"{eth_safe_address_anvil}\n"
        "42\n"
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
        "safe-tx-invalidkey.json\n"
        "q\n"
    )
    if json_path.exists():
        os.remove(json_path)
    subprocess.run(
        MSIG_TX_BUILD,
        input=user_input,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    # Use an invalid key
    invalid_key = "0xZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"
    sign_input = (
        f"{invalid_key}\n"  # private key prompt
        "y\n"  # is right account
        "y\n"  # confirm sign
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


def test_cli_tx_sign_user_abort(temp_msig_workdir, eth_safe_address_anvil):
    """Sign SafeTx but user aborts at confirmation prompt."""
    json_path = temp_msig_workdir / "safe-tx-abort.json"
    user_input = (
        f"{LOCAL_ANVIL_URL}\n"
        f"{eth_safe_address_anvil}\n"
        "42\n"
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
        "safe-tx-abort.json\n"
        "q\n"
    )
    if json_path.exists():
        os.remove(json_path)
    subprocess.run(
        MSIG_TX_BUILD,
        input=user_input,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    owner_key = os.environ.get("ETHEREUM_TEST_PRIVATE_KEY")
    sign_input = (
        f"{owner_key}\n"  # private key prompt
        "y\n"  # is right account
        "n\n"  # user aborts at confirmation
    )
    result = subprocess.run(
        MSIG_TX_SIGN + ["--input-json", str(json_path)],
        input=sign_input,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert "Aborting signing. User declined." in result.stdout
    os.remove(json_path)


def test_cli_tx_sign_missing_json(temp_msig_workdir):
    """Sign SafeTx with missing JSON file (should fail)."""
    missing_path = temp_msig_workdir / "does_not_exist.json"
    sign_input = ""
    result = subprocess.run(
        MSIG_TX_SIGN + ["--input-json", str(missing_path)],
        input=sign_input,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    assert "not found" in result.stdout.lower() or "No such file" in result.stderr


def test_cli_tx_build_and_sign_integration(temp_msig_workdir, eth_safe_address_anvil):
    """Integration: build then sign in sequence, simulating workflow restoration."""
    json_path = temp_msig_workdir / "safe-tx-integrated.json"
    # Build SafeTx JSON
    user_input = (
        f"{LOCAL_ANVIL_URL}\n"
        f"{eth_safe_address_anvil}\n"
        "42\n"
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
        "safe-tx-integrated.json\n"
        "y\n"  # continue to next step (sign)
        f"{os.environ.get('ETHEREUM_TEST_PRIVATE_KEY')}\n"  # private key prompt
        "y\n"  # is right account
        "y\n"  # confirm sign
    )
    if json_path.exists():
        os.remove(json_path)
    result = subprocess.run(
        MSIG_TX_BUILD,
        input=user_input,
        text=True,
        capture_output=True,
        check=True,
        timeout=60,
    )
    assert "SafeTx signed successfully!" in result.stdout
    os.remove(json_path)
