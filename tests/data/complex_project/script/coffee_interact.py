from moccasin.config import get_active_network


def fund_coffee():
    active_network = get_active_network()
    coffee = active_network.manifest_contract("BuyMeACoffee")
    # expecting 0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82
    breakpoint()


def moccasin_main():
    fund_coffee()
