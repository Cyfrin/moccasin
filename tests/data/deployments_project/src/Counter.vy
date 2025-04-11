# SPDX-License-Identifier: MIT
<<<<<<< HEAD
# pragma version ^0.4.1
=======
# pragma version ^0.4.1
>>>>>>> 79aa904 (Bump Vyper version of test contracts to avoid test failings)

number: public(uint256)

@external
def set_number(new_number: uint256):
    self.number = new_number

@external
def increment():
    self.number += 1
