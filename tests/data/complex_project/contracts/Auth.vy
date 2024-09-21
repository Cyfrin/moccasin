# pragma version ^0.4.0

# Not export to importing module?
owner: public(address)

@deploy
def __init__():
    self.owner = msg.sender

def _check_owner():
    assert self.owner == msg.sender

# Must be exported by importing module
@external
def set_owner(owner: address):
    self._check_owner()
    self.owner = owner