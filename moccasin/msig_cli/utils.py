from enum import Enum


################################################################
#                            ENUMS                             #
################################################################
class TransactionType(Enum):
    CONTRACT_CALL = 0
    ERC20_TRANSFER = 1
    RAW = 2


################################################################
#                          EXCEPTIONS                          #
################################################################
# Exception to signal returning to prompt loop
class GoBackToPrompt(Exception):
    pass
