# pragma version 0.4.0

number: public(uint256)

@external
def set_number(new_number: uint256):
    Hello
    self.number = new_number

@external
def increment():
    self.number += 1



