# pragma version 0.4.0
# pragma enable-decimals
# SPDX-License-Identifier: MIT

"""
# @title A sample buy-me-a-coffee contract
# @author Patrick Collins
# @notice This contract is for creating a sample funding contract
"""

from interfaces import AggregatorV3Interface
# interface AggregatorV3Interface:
#     def decimals() -> uint8: view
#     def description() -> String[1000]: view
#     def version() -> uint256: view
#     def getRoundData(_roundId: uint80) -> (uint80, int256, uint256, uint256, uint80): view
#     def latestRoundData() -> (uint80, int256, uint256, uint256, uint80): view

MINIMUM_USD: public(constant(uint256)) = 50 * (10**18)
PRECISION: constant(uint256) = 1 * (10**18)
OWNER: public(immutable(address))

some_value: public(decimal)

funders: public(DynArray[address, 100])
address_to_amount_funded: public(HashMap[address, uint256])
price_feed: public(AggregatorV3Interface)

@deploy
def __init__(price_feed: address):
    self.price_feed = AggregatorV3Interface(price_feed)
    OWNER = msg.sender


@internal
def _only_owner():
    assert msg.sender == OWNER, "Not the contract owner"


@internal
@view
def _get_eth_to_usd_rate(eth_amount: uint256) -> uint256:
    # Check the conversion rate
    a: uint80 = 0
    price: int256 = 0
    b: uint256 = 0
    c: uint256 = 0
    d: uint80 = 0
    (a, price, b, c, d) = staticcall self.price_feed.latestRoundData()
    # We know the price has 8 decimals, so we need to add 10
    eth_price: uint256 = (convert(price, uint256)) * (10**10)
    eth_amount_in_usd: uint256 = (eth_price * eth_amount) // PRECISION
    return eth_amount_in_usd


@external
@payable
def fund():
    usd_value_of_eth: uint256 = self._get_eth_to_usd_rate(msg.value)
    assert usd_value_of_eth >= MINIMUM_USD, "You need to spend more ETH!"
    self.address_to_amount_funded[msg.sender] += msg.value
    self.funders.append(msg.sender)


@external
def withdraw():
    self._only_owner()
    for funder: address in self.funders:
        self.address_to_amount_funded[funder] = 0
    self.funders = []
    send(OWNER, self.balance)


@external
@view
def get_version() -> uint256:
    return staticcall self.price_feed.version()


@external
@view
def get_funder(index: uint256) -> address:
    return self.funders[index]


@external
@view
def get_owner() -> address:
    return OWNER
