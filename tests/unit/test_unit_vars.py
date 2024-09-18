from moccasin.constants.vars import (
    DEFAULT_NETWORKS_BY_CHAIN_ID,
    DEFAULT_NETWORKS_BY_NAME,
)


def test_default_networks_by_name_match_chain_id():
    for chain_id, network in DEFAULT_NETWORKS_BY_CHAIN_ID.items():
        assert DEFAULT_NETWORKS_BY_NAME[network["name"]]["chain_id"] == chain_id
        assert DEFAULT_NETWORKS_BY_CHAIN_ID[chain_id]["name"] == network["name"]


def test_default_networks_by_chain_id_match_name():
    for name, network in DEFAULT_NETWORKS_BY_NAME.items():
        assert DEFAULT_NETWORKS_BY_CHAIN_ID[network["chain_id"]]["name"] == name
        assert DEFAULT_NETWORKS_BY_NAME[name]["chain_id"] == network["chain_id"]
