# pragma version ^0.4.0
import auth

# This contract is not a valid contract. auth.__init__() must be called
# by a contract that imports and uses this contract

uses: auth

pending_owner: address

@deploy
def __init__():
    pass

@external
def begin_transfer(new_owner: address):
    auth._check_owner()
    self.pending_owner = new_owner

@external
def accept_transfer():
    assert msg.sender == self.pending_owner
    auth.owner = msg.sender
    self.pending_owner = empty(address)