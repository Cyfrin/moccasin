from moccasin.commands.from_explorer import boa_get_abi_from_explorer

CURVE_ADDRESS_ETH_MAINNET = "0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E"

# To run this, you'll need EXPLORER_API_KEY set in your environment for an Etherscan API key


def test_boa_get_abi_from_explorer():
    abi = boa_get_abi_from_explorer(CURVE_ADDRESS_ETH_MAINNET, ignore_config=True)
    assert isinstance(abi, list)
    assert len(abi) == 25
