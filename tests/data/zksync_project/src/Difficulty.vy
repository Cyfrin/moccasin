# SPDX-License-Identifier: MIT
# pragma version ^0.4.1

event SampleEvent:
    amount: int128

# Should return 2500000000000000
@external 
@view
def get_difficulty() -> uint256:
    return block.difficulty