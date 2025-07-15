# pragma version >=0.4.0
"""
@license MIT
@author Moccasin Team
@title Counter Contract
@notice A simple contract to demonstrate profiling with a counter.
"""

number: public(uint256)
other_number: public(uint256)


@external
def set_number(new_number: uint256):
    self.number = new_number


@external
def increment():
    self.number += 1
