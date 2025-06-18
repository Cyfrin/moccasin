import os
import subprocess
from pathlib import Path


def test_vyper_help(mox_path):
    """Test vyper command help output."""
    result = subprocess.run(
        [mox_path, "vyper", "--help"], check=True, capture_output=True, text=True
    )
    assert "usage: vyper" in result.stdout
    assert result.returncode == 0


def test_vyper_version(mox_path):
    """Test vyper command version output."""
    result = subprocess.run(
        [mox_path, "vyper", "--version"], check=True, capture_output=True, text=True
    )
    assert result.returncode == 0


def test_vyper_with_contract(complex_temp_path, mox_path):
    """Test vyper command with a contract file."""
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        result = subprocess.run(
            [mox_path, "vyper", "-f", "abi", "contracts/Counter.vy", "--no-install"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)

    # Should contain ABI output
    assert "[" in result.stdout  # JSON array start
    assert result.returncode == 0


def test_vyper_external_interface(complex_temp_path, mox_path):
    """Test vyper command with external interface format."""
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(complex_temp_path))
        result = subprocess.run(
            [
                mox_path,
                "vyper",
                "-f",
                "external_interface",
                "contracts/Counter.vy",
                "--no-install",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)

    # Should contain interface output
    assert "interface" in result.stdout.lower()
    assert result.returncode == 0
