# SPDX-License-Identifier: MIT
# pragma version 0.4.0

@deploy
def __init__():
    selfdestruct(msg.sender)
