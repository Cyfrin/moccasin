# pragma version ^0.4.0

import auth
import UninitializedAuth

initializes: auth
# auth is dependency of auth_2_step
initializes: UninitializedAuth[auth := auth]

# export all external functions
exports: UninitializedAuth.__interface__

@deploy
def __init__():
    auth.__init__()
    UninitializedAuth.__init__()