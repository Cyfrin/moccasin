# from snekmate.auth import ownable as ow
# from snekmate.tokens import erc20
from snekmate.auth import ownable as ow 
from snekmate.tokens import erc20
from PatrickAlphaC.test_repo import my_contract

initializes: ow
initializes: erc20[ownable := ow]

exports: erc20.__interface__


@deploy
@payable
def __init__():
    erc20.__init__("my_token", "MT", 18, "my_token_dapp", "0x02")
    ow.__init__()
