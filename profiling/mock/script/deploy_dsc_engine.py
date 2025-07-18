from src import dsc_engine

from moccasin.boa_tools import VyperContract
from moccasin.config import get_active_network


def deploy_dsc_engine(dsc: VyperContract):
    active_network = get_active_network()
    btc_usd = active_network.manifest_named("btc_usd_price_feed")
    eth_usd = active_network.manifest_named("eth_usd_price_feed")
    wbtc = active_network.manifest_named("wbtc")
    weth = active_network.manifest_named("weth")

    dsc_engine_contract = dsc_engine.deploy(
        [wbtc.address, weth.address], [btc_usd, eth_usd], dsc
    )

    # Verify
    if active_network.has_explorer():
        print("Verifying contract on explorer...")
        result = active_network.moccasin_verify(dsc_engine_contract)
        result.wait_for_verification()
    print(f"Deployed DSC Engine contract at {dsc_engine_contract.address}")

    dsc.set_minter(dsc_engine_contract.address, True)
    dsc.transfer_ownership(dsc_engine_contract.address)

    return dsc_engine_contract


def transfer_ownership(contract_from, address_to):
    contract_from.transfer_ownership(address_to)


def moccasin_main():
    active_network = get_active_network()
    dsc = active_network.manifest_named("decentralized_stable_coin")
    return deploy_dsc_engine(dsc)
