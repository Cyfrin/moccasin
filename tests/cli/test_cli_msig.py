import subprocess
import sys


# @FIXME: make tests for CLI and arguments
def test_cli_tx_builder():
    user_input = (
        "0x1234567890abcdef1234567890abcdef12345678\n"
        "https://mainnet.infura.io/v3/xxx\n"
        "1\n"
        "\n"
        "1\n"
        "0\n"
        "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd\n"
        "0\n"
        "0\n"
        "transfer(address,uint256)\n"
        "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef\n"
        "100\n"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "moccasin.commands.msig",
            "tx",
        ],  # or your CLI entrypoint
        input=user_input,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "SafeTx instance created successfully!" in result.stdout
