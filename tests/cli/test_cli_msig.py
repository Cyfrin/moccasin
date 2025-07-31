import subprocess
import json
import os
import pytest


MOX_CMD = ["mox", "msig", "tx"]


def test_cli_tx_builder_interactive(temp_msig_workdir):
    """Test fully interactive session (all prompts, user saves JSON)."""
    json_path = temp_msig_workdir / "safe-tx.json"
    user_input = (
        # RPC URL (question: What is the RPC URL you want to use to connect to the Ethereum network?)
        "https://sepolia.drpc.org\n"
        # Safe address (question: What is the address of the Safe contract you want to use?)
        "0xcfAAcfc01548Da1478432CF3abdCD1cBDFf11E1C\n"
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
        MOX_CMD,
        input=user_input,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert "SafeTx instance created successfully!" in result.stdout
    assert json_path.exists()
    with open(json_path) as f:
        data = json.load(f)
    assert "types" in data and "message" in data
    assert data["message"]["data"].startswith("0x")
    os.remove(json_path)


def test_cli_tx_builder_args_only(temp_msig_workdir):
    """Test all args provided, no prompts, no JSON output."""
    args = [
        "--rpc-url",
        "https://sepolia.drpc.org",
        "--safe-address",
        "0xcfAAcfc01548Da1478432CF3abdCD1cBDFf11E1C",
        "--to",
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
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
        MOX_CMD + args,
        input="q\n",
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert "SafeTx instance created successfully!" in result.stdout


def test_cli_tx_builder_args_with_json_output(temp_msig_workdir):
    """Test all args provided, with --json-output, file is created and valid."""
    json_path = temp_msig_workdir / "test-tx.json"
    args = [
        "--rpc-url",
        "https://sepolia.drpc.org",
        "--safe-address",
        "0xcfAAcfc01548Da1478432CF3abdCD1cBDFf11E1C",
        "--to",
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
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
        MOX_CMD + args,
        input="q\n",
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert "SafeTx instance created successfully!" in result.stdout
    assert json_path.exists()
    with open(json_path) as f:
        data = json.load(f)
    assert "types" in data and "message" in data
    assert data["message"]["data"].startswith("0x")
    os.remove(json_path)


def test_cli_tx_builder_invalid_json_output(temp_msig_workdir):
    """Test invalid JSON output path (should fail)."""
    args = [
        "--rpc-url",
        "https://sepolia.drpc.org",
        "--safe-address",
        "0xcfAAcfc01548Da1478432CF3abdCD1cBDFf11E1C",
        "--to",
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
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
            MOX_CMD + args,
            input="q\n",
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
