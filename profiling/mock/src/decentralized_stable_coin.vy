# pragma version >=0.4.0
"""
@ license MIT
@ title Decentralized Stable Coin
@ dev Follows the ERC-20 token standard as defined at
     https://eips.ethereum.org/EIPS/eip-20
"""
from ethereum.ercs import IERC20
from ethereum.ercs import IERC20Detailed
from snekmate.auth import ownable as ow
from snekmate.tokens import erc20
from src.interfaces import i_decentralized_stable_coin

implements: IERC20
implements: IERC20Detailed
implements: i_decentralized_stable_coin

initializes: ow
initializes: erc20[ownable := ow]

NAME: constant(String[25]) = "Decentralized Stable Coin"
SYMBOL: constant(String[5]) = "DSC"
DECIMALS: constant(uint8) = 18
EIP712_VERSOIN: constant(String[20]) = "1"


@deploy
def __init__():
    ow.__init__()
    erc20.__init__(NAME, SYMBOL, DECIMALS, NAME, EIP712_VERSOIN)


exports: (
    erc20.IERC20,
    erc20.IERC20Detailed,
    erc20.burn_from,
    erc20.mint,
    erc20.set_minter,
    ow.owner,
    ow.transfer_ownership,
)
