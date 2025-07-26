from enum import Enum


# --- Enums ---
class OperationType(Enum):
    """Enum for different types of operations in a multisig contract."""

    CALL = 0
    DELEGATECALL = 1
    # fill in other operation types as needed


class TransactionType(Enum):
    """Enum for different types of transactions in a multisig contract."""

    CONTRACT_CALL = 0
    ERC20_TRANSFER = 1
    ERC721_1155_TRANSFER = 2
    RAW_TRANSACTION = 3
    # fill in other transaction types as needed
