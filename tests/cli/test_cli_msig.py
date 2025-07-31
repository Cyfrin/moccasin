import subprocess
import json
import os
import pytest


MOX_CMD = ["mox", "msig", "tx"]


# Fixture for a temporary working directory
@pytest.fixture
def temp_workdir(tmp_path, monkeypatch):
    """Create a temporary working directory for tests.

    @dev The tmp_path argument in your fixture is a built-in pytest fixture.
    When you use pytest for testing, it provides tmp_path automatically
    to your test functions and fixtures.
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_cli_tx_builder_interactive(temp_workdir):
    """Test fully interactive session (all prompts, user saves JSON)."""
    json_path = temp_workdir / "safe-tx.json"
    user_input = (
        "https://sepolia.drpc.org\n"
        "0xcfAAcfc01548Da1478432CF3abdCD1cBDFf11E1C\n"
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
        "safe-tx.json\n"
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


def test_cli_tx_builder_args_only(temp_workdir):
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
        MOX_CMD + args, input="", text=True, capture_output=True, check=True, timeout=30
    )
    assert "SafeTx instance created successfully!" in result.stdout


def test_cli_tx_builder_args_with_json_output(temp_workdir):
    """Test all args provided, with --json-output, file is created and valid."""
    json_path = temp_workdir / "test-tx.json"
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
        MOX_CMD + args, input="", text=True, capture_output=True, check=True, timeout=30
    )
    assert "SafeTx instance created successfully!" in result.stdout
    assert json_path.exists()
    with open(json_path) as f:
        data = json.load(f)
    assert "types" in data and "message" in data
    assert data["message"]["data"].startswith("0x")
    os.remove(json_path)


def test_cli_tx_builder_invalid_json_output(temp_workdir):
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
            input="",
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
