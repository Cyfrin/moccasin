import os
from moccasin.commands.explorer import boa_get_abi_from_explorer

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
        ignore_config=True,
    )
    assert isinstance(abi, list)
    assert len(abi) == 26


def test_boa_get_abi_from_explorer_by_name(complex_project_config):
    abi = boa_get_abi_from_explorer(
        LINK_ADDRESS_OPT_MAINNET, network_name_or_id="optimism"
    )
    assert isinstance(abi, list)
    assert len(abi) == 26


def test_boa_get_abi_from_explorer_by_chain_id(complex_project_config):
    abi = boa_get_abi_from_explorer(LINK_ADDRESS_OPT_MAINNET, network_name_or_id="10")
    assert isinstance(abi, list)
    assert len(abi) == 26