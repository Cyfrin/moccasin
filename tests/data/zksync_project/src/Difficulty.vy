# SPDX-License-Identifier: MIT
<<<<<<< HEAD
# pragma version ^0.4.1

event SampleEvent:
    amount: int128
=======
# pragma version ^0.4.1
>>>>>>> 79aa904 (Bump Vyper version of test contracts to avoid test failings)

# Should return 2500000000000000
@external 
@view
def get_difficulty() -> uint256:
    return block.difficulty