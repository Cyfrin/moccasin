# SPDX-License-Identifier: MIT
# pragma version ^0.4.1

@deploy
def __init__():
    selfdestruct(msg.sender)
