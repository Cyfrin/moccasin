# pragma version >=0.4.0
"""
@title mock_token
@license MIT
"""
# @dev We import and implement the `IERC20` interface,
# which is a built-in interface of the Vyper compiler.
from ethereum.ercs import IERC20

implements: IERC20

from ethereum.ercs import IERC20Detailed

implements: IERC20Detailed

# @dev We import and initialise the `ownable` module.
from snekmate.auth import ownable as ow

initializes: ow

# @dev We import and initialise the `erc20` module.
from snekmate.tokens import erc20

initializes: erc20[ownable := ow]

exports: erc20.__interface__

NAME: constant(String[25]) = "Mock WETH"
SYMBOL: constant(String[5]) = "MWETH"
DECIMALS: constant(uint8) = 18
EIP712_VERSOIN: constant(String[20]) = "1"


@deploy
def __init__():
    ow.__init__()
    erc20.__init__(NAME, SYMBOL, DECIMALS, NAME, EIP712_VERSOIN)


@external
def mock_mint():
    """
    @notice Mint 100 tokens to the caller.
    """
    erc20._mint(msg.sender, 10 * 10**18)


@external
def mint_amount(amount: uint256):
    """
    @notice Mint `amount` tokens to the caller.
    """
    erc20._mint(msg.sender, amount)
