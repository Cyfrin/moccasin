from moccasin.config import get_active_network


def moccasin_main():
    active_network = get_active_network()
    contract = active_network.get_latest_contract_checked("Difficulty")
    print("Contract is: ", contract)
