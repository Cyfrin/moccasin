# @TODO test the full workflow of the CLI msig commands: build, sign, execute
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
#                      TX_BUILD & TX_SIGN                      #
################################################################
def test_cli_tx_build_and_sign_integration(
    mox_path, moccasin_home_folder, eth_safe_address_anvil
):
    """Integration: build then sign in sequence, simulating workflow restoration."""
    json_path = moccasin_home_folder / "safe-tx-integrated.json"
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
        "n\n"  # not MoccasinAccount
        f"{os.environ.get('ETHEREUM_TEST_PRIVATE_KEY')}\n"
        "y\n"  # confirm account
        "y\n"  # confirm signing
    )
    if json_path.exists():
        os.remove(json_path)

    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(moccasin_home_folder))
        result = subprocess.run(
            [mox_path, "msig", "tx-build"],
            input=user_input,
            text=True,
            capture_output=True,
            check=True,
            timeout=60,
        )
    finally:
        os.chdir(current_dir)

    assert "SafeTx signed successfully!" in result.stdout
    os.remove(json_path)
