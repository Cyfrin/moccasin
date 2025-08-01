import re
from pathlib import Path

from argparse import ArgumentParser
from eth_abi.abi import is_encodable_type
from eth_utils import is_address, is_hex, is_0x_prefixed, to_checksum_address, to_bytes
from eth_utils.address import ChecksumAddress
from prompt_toolkit.validation import Validator
from moccasin.msig_cli.constants import (
    ERROR_INVALID_ADDRESS,
    ERROR_INVALID_RPC_URL,
    ERROR_INVALID_NUMBER,
    ERROR_INVALID_NOT_ZERO_NUMBER,
    ERROR_INVALID_OPERATION,
    ERROR_INVALID_DATA,
    ERROR_INVALID_TRANSACTION_TYPE,
    ERROR_INVALID_FUNCTION_SIGNATURE,
    ERROR_INVALID_BOOLEAN,
    ERROR_INVALID_JSON_FILE,
)
from moccasin.msig_cli.utils import TransactionType
from safe_eth.safe.multi_send import MultiSendOperation


################################################################
#                       CORE VALIDATORS                        #
################################################################
def is_valid_address(address: str) -> bool:
    """Check if the provided address is a valid address."""
    return is_address(address)


def is_valid_rpc_url(rpc_url: str) -> bool:
    """Check if the provided RPC URL is valid."""
    return rpc_url.startswith("http://") or rpc_url.startswith("https://")


def is_valid_number(value: str) -> bool:
    """Check if the provided value is a valid number."""
    return value.isdigit() and int(value) >= 0


def is_valid_not_zero_number(value: str) -> bool:
    """Check if the provided value is a valid positive number."""
    return value.isdigit() and int(value) > 0


def is_valid_operation(value: str) -> bool:
    """Check if the provided value is a valid operation type."""
    return value.isdigit() and int(value) in [op.value for op in MultiSendOperation]


def is_valid_data(data: str) -> bool:
    """Check if the provided data is a valid hex string for calldata using eth_utils.is_hex."""
    return is_0x_prefixed(data) and is_hex(data)


def is_valid_transaction_type(value: str) -> bool:
    """Check if the provided value is a valid transaction type."""
    return value.isdigit() and int(value) in [tx.value for tx in TransactionType]


def is_valid_function_signature(sig: str) -> bool:
    """Check if the provided function signature is valid.

    Must match: name(args) where name is a valid identifier and args can be empty or comma-separated types.
    """
    # Use a raw string and single backslashes for regex
    m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\(([^()]*)\)$", sig)
    if not m:
        return False
    types = m.group(2)
    if types.strip() == "":
        return True
    for typ in types.split(","):
        if not is_encodable_type(typ.strip()):
            return False
    return True


def is_valid_boolean(value: str) -> bool:
    """Check if the provided value is a valid boolean."""
    return value in ("true", "false")


def is_json_file(value: str) -> bool:
    """Check if the provided value is a valid JSON file path (ends with .json and not a directory)."""
    path = Path(value)
    return value.lower().endswith(".json") and not path.is_dir()


# Generic non-empty validator
def is_not_empty(value: str) -> bool:
    """Generic non-empty validator."""
    return value != ""


################################################################
#                      PROMPT VALIDATORS                       #
################################################################
def allow_empty(core_validator):
    """Decorator to allow empty input for a validator."""

    def wrapper(value):
        if value == "":
            return True
        return core_validator(value)

    return wrapper


validator_address = Validator.from_callable(
    allow_empty(is_valid_address),
    error_message=ERROR_INVALID_ADDRESS,
    move_cursor_to_end=True,
)

validator_safe_address = Validator.from_callable(
    is_valid_address, error_message=ERROR_INVALID_ADDRESS, move_cursor_to_end=True
)

validator_rpc_url = Validator.from_callable(
    is_valid_rpc_url, error_message=ERROR_INVALID_RPC_URL, move_cursor_to_end=True
)

validator_number = Validator.from_callable(
    allow_empty(is_valid_number),
    error_message=ERROR_INVALID_NUMBER,
    move_cursor_to_end=True,
)

validator_not_zero_number = Validator.from_callable(
    allow_empty(is_valid_not_zero_number),
    error_message=ERROR_INVALID_NOT_ZERO_NUMBER,
    move_cursor_to_end=True,
)

validator_transaction_type = Validator.from_callable(
    allow_empty(is_valid_transaction_type),
    error_message=ERROR_INVALID_TRANSACTION_TYPE,
    move_cursor_to_end=True,
)

validator_operation = Validator.from_callable(
    allow_empty(is_valid_operation),
    error_message=ERROR_INVALID_OPERATION,
    move_cursor_to_end=True,
)

validator_data = Validator.from_callable(
    is_valid_data, error_message=ERROR_INVALID_DATA, move_cursor_to_end=True
)


validator_function_signature = Validator.from_callable(
    is_valid_function_signature,
    error_message=ERROR_INVALID_FUNCTION_SIGNATURE,
    move_cursor_to_end=True,
)

validator_boolean = Validator.from_callable(
    is_valid_boolean, error_message=ERROR_INVALID_BOOLEAN, move_cursor_to_end=True
)

validator_not_empty = Validator.from_callable(
    is_not_empty, error_message="Value cannot be empty.", move_cursor_to_end=True
)

validator_json_file = Validator.from_callable(
    is_json_file, error_message=ERROR_INVALID_JSON_FILE, move_cursor_to_end=True
)

# --- Type-based prompt validation for function parameters ---
param_type_validators = {
    "address": validator_address,
    "uint256": validator_number,
    "uint": validator_number,
    "int256": validator_number,
    "int": validator_number,
    "bool": validator_boolean,
    # @TODO Add more complex types like bytes, arrays, etc.
}


################################################################
#                     ARGPARSE VALIDATORS                      #
################################################################
def validate_address(value: str) -> ChecksumAddress:
    """Validate and return a checksum address."""
    if not is_valid_address(value):
        raise ValueError(ERROR_INVALID_ADDRESS)
    return to_checksum_address(value)


def validate_rpc_url(value: str) -> str:
    """Validate and return a valid RPC URL."""
    if not is_valid_rpc_url(value):
        raise ValueError(ERROR_INVALID_RPC_URL)
    return value


def validate_number(value: str) -> int:
    """Validate and return a valid number."""
    if not is_valid_number(value):
        raise ValueError(ERROR_INVALID_NUMBER)
    return int(value)


def validate_data(value: str) -> bytes:
    """Validate and return a valid hex string for calldata."""
    if not is_valid_data(value):
        raise ValueError(ERROR_INVALID_DATA)
    return to_bytes(hexstr=value)


def validate_json_file(value: str) -> Path:
    """Validate and return a valid JSON file path."""
    if not is_json_file(value):
        raise ValueError("Invalid JSON file path. Please provide a valid .json file.")
    return Path(value)


################################################################
#                        MSIG ARGPARSE                         #
################################################################
def add_tx_builder_args(parser: ArgumentParser):
    """Add transaction builder arguments to the parser."""
    parser.add_argument(
        "--rpc-url",
        help="RPC URL to get the Safe contract from.",
        type=validate_rpc_url,
    )
    parser.add_argument(
        "--safe-address",
        help="Address of the Safe contract to build the transaction for.",
        type=validate_address,
    )
    parser.add_argument(
        "--to", help="Address of the contract to call.", type=validate_address
    )
    parser.add_argument(
        "--operation",
        help="Operation type: 0 for call, 1 for delegate call.",
        type=validate_number,
    )
    parser.add_argument(
        "--value",
        help="Value to send with the transaction, in wei.",
        type=validate_number,
    )
    parser.add_argument(
        "--data",
        help="Data to send with the transaction, in hex format.",
        type=validate_data,
    )
    parser.add_argument(
        "--safe-nonce",
        help="Nonce of the Safe contract to use for the transaction.",
        type=validate_number,
    )
    parser.add_argument(
        "--gas-token",
        help="Token to use for gas, defaults to the native token of the network.",
        type=validate_address,
    )
    parser.add_argument(
        "--json-output",
        help="Output file to save the EIP-712 structured data as JSON.",
        type=validate_json_file,
    )
