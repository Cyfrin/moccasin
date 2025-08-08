from typing import TypedDict, List


################################################################
#                            TYPES                             #
################################################################
class T_SafeTxMessage(TypedDict):
    to: str
    value: int
    data: str
    operation: int
    safeTxGas: int
    baseGas: int
    dataGas: int
    gasPrice: int
    gasToken: str
    refundReceiver: str
    nonce: int


class T_EIP712TypeField(TypedDict):
    name: str
    type: str


class T_EIP712Domain(TypedDict):
    verifyingContract: str
    chainId: int


class T_EIP712Types(TypedDict):
    EIP712Domain: List[T_EIP712TypeField]
    SafeTx: List[T_EIP712TypeField]


class T_EIP712TxJson(TypedDict):
    types: T_EIP712Types
    primaryType: str
    domain: T_EIP712Domain
    message: T_SafeTxMessage


class T_SafeTxData(TypedDict):
    safeTx: T_EIP712TxJson
    signatures: str  # Signature data in hex format
