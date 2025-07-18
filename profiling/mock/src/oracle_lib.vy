# pragma version >=0.4.0
"""
@ license MIT
@ title oracle_lib
@ author You!
@ notice This library is used to check the Chainlink Oracle for stale data.
    If a price is stale, functions will revert, and render the DSCEngine unusable - this is by design.
    We want the DSCEngine to freeze if prices become stale.

    So if the Chainlink network explodes and you have a lot of money locked in the protocol... too bad.
"""
from interfaces import AggregatorV3Interface

TIMEOUT: constant(uint256) = 3 * 3600


@external
@view
def stale_check_latest_round_data(
    chainlink_feed: address,
) -> (uint80, int256, uint256, uint256, uint80):
    return self._stale_check_latest_round_data(chainlink_feed)


@internal
@view
def _stale_check_latest_round_data(
    price_price_address: address,
) -> (uint80, int256, uint256, uint256, uint80):
    price_price: AggregatorV3Interface = AggregatorV3Interface(
        price_price_address
    )

    round_id: uint80 = 0
    price: int256 = 0
    started_at: uint256 = 0
    updated_at: uint256 = 0
    answered_in_round: uint80 = 0
    (
        round_id, price, started_at, updated_at, answered_in_round
    ) = staticcall price_price.latestRoundData()

    assert updated_at != 0, "DSCEngine_StalePrice"
    assert answered_in_round >= round_id, "DSCEngine_StalePrice"

    seconds_since: uint256 = block.timestamp - updated_at
    assert seconds_since <= TIMEOUT, "DSCEngine_StalePrice"

    return (round_id, price, started_at, updated_at, answered_in_round)
