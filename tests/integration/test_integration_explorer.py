import os
import subprocess
from pathlib import Path

from moccasin.commands.explorer import boa_get_abi_from_explorer
from tests.conftest import COMPLEX_PROJECT_PATH

CURVE_ADDRESS_ETH_MAINNET = "0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E"
LINK_ADDRESS_OPT_MAINNET = "0x350a791Bfc2C21F9Ed5d10980Dad2e2638ffa7f6"


def test_boa_get_abi_from_explorer_ignore_config_default():
    abi = boa_get_abi_from_explorer(CURVE_ADDRESS_ETH_MAINNET, ignore_config=True)
    assert isinstance(abi, list)
    assert len(abi) == 25


def test_boa_get_abi_from_explorer_ignore_config_id():
    abi = boa_get_abi_from_explorer(
        LINK_ADDRESS_OPT_MAINNET,
        network_name_or_id="10",
        api_key=os.getenv("OPTIMISTIC_ETHERSCAN_API_KEY"),
        explorer_uri="https://api-optimistic.etherscan.io/api",
        ignore_config=True,
    )
    assert isinstance(abi, list)
    assert len(abi) == 26


def test_boa_get_abi_from_explorer_by_name(complex_project_config):
    abi = boa_get_abi_from_explorer(
        LINK_ADDRESS_OPT_MAINNET,
        network_name_or_id="optimism",
        explorer_uri="https://api-optimistic.etherscan.io/api",
    )
    assert isinstance(abi, list)
    assert len(abi) == 26


def test_boa_get_abi_from_explorer_by_chain_id(complex_project_config):
    abi = boa_get_abi_from_explorer(
        LINK_ADDRESS_OPT_MAINNET,
        network_name_or_id="10",
        explorer_uri="https://api-optimistic.etherscan.io/api",
    )
    assert isinstance(abi, list)
    assert len(abi) == 26


def test_get_abi_from_script_etherscan(mox_path, complex_project_config):
    current_dir = Path.cwd()
    os.chdir(COMPLEX_PROJECT_PATH)
    try:
        result = subprocess.run(
            [mox_path, "run", "get_usdc_balance", "--network", "mainnet_fork"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert int(result.stdout) == 6
