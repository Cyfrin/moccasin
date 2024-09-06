# SPDX-License-Identifier: MIT
# @version 0.3.10

number: public(uint256)


@external
def set_number(new_number: uint256):
    self.number = new_number


@external
def increment():
    self.number += 1
