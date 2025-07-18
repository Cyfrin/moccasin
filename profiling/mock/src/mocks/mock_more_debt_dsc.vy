# pragma version >=0.4.0
"""
@ title MockMoreDebtDSC
@ license MIT
"""
from ethereum.ercs import IERC20

implements: IERC20

from ethereum.ercs import IERC20Detailed

implements: IERC20Detailed

from src.interfaces import AggregatorV3Interface

from snekmate.auth import ownable as ow

initializes: ow

from snekmate.tokens import erc20

initializes: erc20[ownable := ow]

# Constants
NAME: constant(String[25]) = "DecentralizedStableCoin"
SYMBOL: constant(String[5]) = "DSC"
DECIMALS: constant(uint8) = 18
EIP712_VERSION: constant(String[20]) = "1"

# State Variables
mock_aggregator: public(AggregatorV3Interface)


@deploy
def __init__(_mock_aggregator: address):
    """
    @notice Contract constructor
    @param _mock_aggregator The address of price feed aggregator
    """
    ow.__init__()
    erc20.__init__(NAME, SYMBOL, DECIMALS, NAME, EIP712_VERSION)
    self.mock_aggregator = AggregatorV3Interface(_mock_aggregator)


@external
def burn_from(_from: address, _amount: uint256):
    """
    @notice Burns tokens and crashes the price
    @param _amount Amount of tokens to burn
    """
    assert _amount > 0, "Amount must be more than zero"
    extcall self.mock_aggregator.updateAnswer(0)
    erc20._burn(_from, _amount)


exports: (
    erc20.IERC20,
    erc20.IERC20Detailed,
    erc20.mint,
    erc20.set_minter,
    ow.owner,
    ow.transfer_ownership,
)
