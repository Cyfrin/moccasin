# SPDX-License-Identifier: MIT
<<<<<<< HEAD
# pragma version ^0.4.1
=======
# pragma version ^0.4.1
>>>>>>> 79aa904 (Bump Vyper version of test contracts to avoid test failings)

@deploy
def __init__():
    selfdestruct(msg.sender)
