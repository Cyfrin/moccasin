import re
from pathlib import Path

from eth_abi.abi import is_encodable_type
from eth_utils import is_0x_prefixed, is_address, is_hex, to_bytes, to_checksum_address
from eth_utils.address import ChecksumAddress
from prompt_toolkit.validation import Validator
from safe_eth.safe.multi_send import MultiSendOperation

from moccasin.msig_cli.constants import (
    ERROR_INVALID_ADDRESS,
    ERROR_INVALID_BOOLEAN,
    ERROR_INVALID_DATA,
    ERROR_INVALID_FUNCTION_SIGNATURE,
    ERROR_INVALID_JSON_FILE,
    ERROR_INVALID_NOT_ZERO_NUMBER,
    ERROR_INVALID_NUMBER,
    ERROR_INVALID_OPERATION,
    ERROR_INVALID_RPC_URL,
    ERROR_INVALID_TRANSACTION_TYPE,
    ERROR_INVALID_TXT_FILE,
    ERROR_INVALID_SIGNATURES_INPUT,
    ERROR_INVALID_SIGNER,
    ERROR_INVALID_PRIVATE_KEY,
)
from moccasin.msig_cli.utils import TransactionType


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


def is_valid_json_file(value: str) -> bool:
    """Check if the provided value is a valid JSON file path (ends with .json and not a directory)."""
    path = Path(value)
    return value.lower().endswith(".json") and not path.is_dir()


def is_valid_signatures_input(value: str) -> bool:
    """Check if the provided value is a valid signatures input."""
    # Check if it's a path to a file
    path = Path(value)
    if path.is_file():
        return value.lower().endswith(".txt") and not path.is_dir()
    # Check if it's a hex string
    return is_0x_prefixed(value) and is_hex(value)


def is_valid_private_key(value: str) -> bool:
    """Check if the provided value is a valid private key."""
    # A valid private key is a 64-character hex string with 0x prefix
    return is_0x_prefixed(value) and is_hex(value) and len(value) == 66


def is_valid_signer(value: str) -> bool:
    """Check if the provided value is a valid signer input."""
    # A valid signer can be an account name or a private key
    return is_valid_private_key(value) or is_not_empty(value)


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
    is_valid_json_file, error_message=ERROR_INVALID_JSON_FILE, move_cursor_to_end=True
)

validator_signatures = Validator.from_callable(
    is_valid_signatures_input,
    error_message=ERROR_INVALID_SIGNATURES_INPUT,
    move_cursor_to_end=True,
)

validator_private_key = Validator.from_callable(
    is_valid_private_key,
    error_message=ERROR_INVALID_PRIVATE_KEY,
    move_cursor_to_end=True,
)

validator_signer = Validator.from_callable(
    is_valid_signer, error_message=ERROR_INVALID_SIGNER, move_cursor_to_end=True
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
    if not is_valid_json_file(value):
        raise ValueError(ERROR_INVALID_JSON_FILE)
    return Path(value)


def validate_signatures_input(value: str) -> str:
    """Validate and return a valid signatures input."""
    if not is_valid_signatures_input(value):
        raise ValueError(ERROR_INVALID_SIGNATURES_INPUT)
    return value


def validate_signer(value: str) -> str:
    """Validate and return a valid signer input."""
    if not is_valid_signer(value):
        raise ValueError(ERROR_INVALID_SIGNER)
    return value
