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
    ERROR_INVALID_PRIVATE_KEY,
    ERROR_INVALID_RPC_URL,
    ERROR_INVALID_TX_BUILD_DATA_TYPE,
)
from moccasin.msig_cli.utils.enums import TxBuildDataType


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


def is_valid_bytes_hex(value: str) -> bool:
    """Check if the provided value is a valid bytes string."""
    return is_0x_prefixed(value) and is_hex(value)


def is_valid_operation(value: str) -> bool:
    """Check if the provided value is a valid operation type."""
    return value.isdigit() and int(value) in [op.value for op in MultiSendOperation]


def is_valid_tx_build_data_type(value: str) -> bool:
    """Check if the provided value is a valid transaction type."""
    return value.isdigit() and int(value) in [tx.value for tx in TxBuildDataType]


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


def is_valid_private_key(value: str) -> bool:
    """Check if the provided value is a valid private key."""
    # A valid private key is a 64-character hex string with 0x prefix
    return is_0x_prefixed(value) and is_hex(value) and len(value) == 66


def is_valid_string(value: str) -> bool:
    """Check if the provided value is a valid string."""
    return isinstance(value, str)


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


# --- Validators allowing empty input ---
validator_empty_or_address = Validator.from_callable(
    allow_empty(is_valid_address),
    error_message=ERROR_INVALID_ADDRESS,
    move_cursor_to_end=True,
)

validator_empty_or_number = Validator.from_callable(
    allow_empty(is_valid_number),
    error_message=ERROR_INVALID_NUMBER,
    move_cursor_to_end=True,
)

validator_empty_or_not_zero_number = Validator.from_callable(
    allow_empty(is_valid_not_zero_number),
    error_message=ERROR_INVALID_NOT_ZERO_NUMBER,
    move_cursor_to_end=True,
)

validator_empty_or_operation = Validator.from_callable(
    allow_empty(is_valid_operation),
    error_message=ERROR_INVALID_OPERATION,
    move_cursor_to_end=True,
)

validator_empty_or_tx_build_data_type = Validator.from_callable(
    allow_empty(is_valid_tx_build_data_type),
    error_message=ERROR_INVALID_TX_BUILD_DATA_TYPE,
    move_cursor_to_end=True,
)

validator_empty_or_bytes_hex = Validator.from_callable(
    allow_empty(is_valid_bytes_hex),
    error_message=ERROR_INVALID_DATA,
    move_cursor_to_end=True,
)

validator_empty_or_boolean = Validator.from_callable(
    allow_empty(is_valid_boolean),
    error_message=ERROR_INVALID_BOOLEAN,
    move_cursor_to_end=True,
)

validator_empty_or_function_signature = Validator.from_callable(
    allow_empty(is_valid_function_signature),
    error_message=ERROR_INVALID_FUNCTION_SIGNATURE,
    move_cursor_to_end=True,
)

validator_empty_or_string = Validator.from_callable(
    allow_empty(is_valid_string),
    error_message="Invalid string input.",
    move_cursor_to_end=True,
)

# --- Validators not allowing empty input ---
validator_address = Validator.from_callable(
    is_valid_address, error_message=ERROR_INVALID_ADDRESS, move_cursor_to_end=True
)


validator_safe_address = Validator.from_callable(
    is_valid_address, error_message=ERROR_INVALID_ADDRESS, move_cursor_to_end=True
)

validator_rpc_url = Validator.from_callable(
    is_valid_rpc_url, error_message=ERROR_INVALID_RPC_URL, move_cursor_to_end=True
)

validator_number = Validator.from_callable(
    is_valid_number, error_message=ERROR_INVALID_NUMBER, move_cursor_to_end=True
)

validator_bytes_hex = Validator.from_callable(
    is_valid_bytes_hex, error_message=ERROR_INVALID_DATA, move_cursor_to_end=True
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

validator_private_key = Validator.from_callable(
    is_valid_private_key,
    error_message=ERROR_INVALID_PRIVATE_KEY,
    move_cursor_to_end=True,
)

validator_string = Validator.from_callable(
    is_valid_string, error_message="Invalid string input.", move_cursor_to_end=True
)


# --- Type-based prompt validation for function parameters ---
def get_param_validator(abi_type: str) -> Validator:
    """Return the appropriate validator based on the Ethereum ABI type.

    :param abi_type: The Ethereum ABI type (e.g., "uint256", "address", "bool", etc.).
    """
    # Handle array types like address[], uint256[], etc.
    array_match = re.match(r"^(.*)\[\]$", abi_type)
    if array_match:
        element_type = array_match.group(1)
        return _make_array_validator(element_type)

    # Handle basic types
    if abi_type == "address":
        return validator_empty_or_address
    if abi_type == "bool":
        return validator_empty_or_boolean
    if re.match(r"^uint[0-9]*$", abi_type) or re.match(r"^int[0-9]*$", abi_type):
        return validator_empty_or_number
    if re.match(r"^bytes[0-9]*$", abi_type):
        return validator_empty_or_bytes_hex
    # Allow empty for other types (string, etc...)
    if abi_type == "string":
        return validator_empty_or_string
    # Fallback to a generic non-empty validator
    return validator_not_empty


# --- Array validator for ABI array types ---
def _make_array_validator(element_type: str) -> Validator:
    """
    Returns a Validator for an array of the given element_type.
    The input should be a comma-separated string.
    :param element_type: The type of the array elements (e.g., "address", "uint256", etc.).
    :return: A Validator instance that checks if the input is a valid comma-separated array of the specified type.
    """

    # Recursively get the validator for the element type
    def validate_array(value: str) -> bool:
        """Validate a comma-separated array of values."""
        if value == "":
            return True  # Allow empty input for optional arrays
        elements = [v.strip() for v in value.split(",")]
        for elem in elements:
            try:
                _validate_array_values_from_type(element_type, elem)
            except Exception:
                return False
        return True

    return Validator.from_callable(
        validate_array,
        error_message=f"Invalid array of {element_type}. Comma-separated values required.",
        move_cursor_to_end=True,
    )


def _validate_array_values_from_type(element_type: str, value: str):
    """Validate a single value against the specified element type.

    :param element_type: The type of the array elements (e.g., "address", "uint256", etc.).
    :param value: The value to validate.
    :raises Exception if validation fails.
    """
    if element_type == "address":
        if not is_valid_address(value):
            raise Exception
    elif re.match(r"^uint[0-9]*$", element_type) or re.match(
        r"^int[0-9]*$", element_type
    ):
        if not is_valid_number(value):
            raise Exception
    elif element_type == "bool":
        if value not in ("true", "false"):
            raise Exception
    elif re.match(r"^bytes[0-9]*$", element_type):
        if not is_valid_bytes_hex(value):
            raise Exception
    elif element_type == "string":
        if not is_valid_string(value):
            raise Exception


################################################################
#                     ARGPARSE VALIDATORS                      #
################################################################
def validate_address(value: str) -> ChecksumAddress:
    """Validate and return a checksum address."""
    if not is_valid_address(value):
        raise ValueError(ERROR_INVALID_ADDRESS)
    return to_checksum_address(value)


def validate_number(value: str) -> int:
    """Validate and return a valid number."""
    if not is_valid_number(value):
        raise ValueError(ERROR_INVALID_NUMBER)
    return int(value)


def validate_data(value: str) -> bytes:
    """Validate and return a valid hex string for calldata."""
    if not is_valid_bytes_hex(value):
        raise ValueError(ERROR_INVALID_DATA)
    return to_bytes(hexstr=value)


def validate_json_file(value: str) -> Path:
    """Validate and return a valid JSON file path."""
    if not is_valid_json_file(value):
        raise ValueError(ERROR_INVALID_JSON_FILE)
    return Path(value)
