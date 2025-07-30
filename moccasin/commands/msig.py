from argparse import ArgumentParser, Namespace
from enum import Enum
from eth_typing import ChecksumAddress
from eth_utils import (
    to_bytes,
    to_checksum_address,
    is_address,
    is_hex,
    function_signature_to_4byte_selector,
)
from eth.constants import ZERO_ADDRESS

from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.shortcuts import clear as prompt_clear
from prompt_toolkit.validation import Validator

from moccasin.logging import logger

from safe_eth.eth import EthereumClient
from safe_eth.safe import Safe
from safe_eth.safe.multi_send import MultiSend, MultiSendTx, MultiSendOperation


# --- Enums ---
class TransactionType(Enum):
    CONTRACT_CALL = 0
    ERC20_TRANSFER = 1
    RAW = 2


# --- Core Validators ---
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
    return is_hex(data)


def is_valid_transaction_type(value: str) -> bool:
    """Check if the provided value is a valid transaction type."""
    return value.isdigit() and int(value) in [tx.value for tx in TransactionType]


def is_valid_function_signature(sig: str) -> bool:
    """Check if the provided function signature is valid by trying to get its 4-byte selector."""
    try:
        function_signature_to_4byte_selector(sig)
        return True
    except Exception:
        return False


def is_valid_boolean(value: str) -> bool:
    """Check if the provided value is a valid boolean."""
    return value in ("true", "false")


# Generic non-empty validator
def is_not_empty(value: str) -> bool:
    """Generic non-empty validator."""
    return value != ""


# --- Error constants ---
ERROR_INVALID_ADDRESS = "Invalid address format. Please enter a valid checksum address."
ERROR_INVALID_RPC_URL = "Invalid RPC URL format. Please enter a valid URL starting with http:// or https://."
ERROR_INVALID_NUMBER = "Invalid number format. Please enter a valid integer."
ERROR_INVALID_NOT_ZERO_NUMBER = (
    "Invalid non zero number format. Please enter a valid non zero positive integer."
)
ERROR_INVALID_OPERATION = "Invalid operation type. Please enter a valid operation type (0 for call, 1 for delegate call)."
ERROR_INVALID_DATA = (
    "Invalid data format. Please enter a valid hex string for calldata."
)
ERROR_INVALID_TRANSACTION_TYPE = "Invalid transaction type. Please enter a valid transaction type (0 for contract call, 1 for ERC20 transfer, 2 for raw)."
ERROR_INVALID_FUNCTION_SIGNATURE = (
    "Invalid function signature. Example: transfer(address,uint256)"
)


# --- Prompt Validators ---
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
    is_valid_boolean,
    error_message="Invalid boolean value. Please enter true/false",
    move_cursor_to_end=True,
)

validator_not_empty = Validator.from_callable(
    is_not_empty, error_message="Value cannot be empty.", move_cursor_to_end=True
)

# --- Type-based prompt validation for function parameters ---
param_type_validators = {
    "address": validator_address,
    "uint256": validator_number,
    "uint": validator_number,
    "int256": validator_number,
    "int": validator_number,
    "bool": validator_boolean,
}


# --- Argparse Validators ---
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


# --- Main Function ---
def main(args: Namespace) -> int:
    if args.msig_command == "tx":
        # Base parameter for a Safe instantiation
        rpc_url: str = getattr(args, "rpc_url", None)
        safe_address: ChecksumAddress = getattr(args, "safe_address", None)
        safe_instance: Safe = None

        # Parameters for the SafeTx instantiation from user input
        to: ChecksumAddress = getattr(args, "to", None)
        value: int = getattr(args, "value", 0)
        operation: int = getattr(args, "operation", 0)
        safe_nonce: int = getattr(args, "safe_nonce", 0)
        data: bytes = getattr(args, "data", b"")
        gas_token: ChecksumAddress = getattr(args, "gas_token", None)

        # Create a prompt session with auto-suggest and a bottom toolbar
        prompt_session = PromptSession(
            auto_suggest=AutoSuggestFromHistory(),
            bottom_toolbar="Tips: Use Ctrl-C to exit.",
            validate_while_typing=False,
        )

        # Intitialize Safe instance
        prompt_clear()
        print_formatted_text(
            HTML("\n<b><magenta>Initializing Safe instance...</magenta></b>\n")
        )

        def _try_initialize_safe_instance(rpc_url, safe_address):
            """Try to initialize a Safe instance with the provided RPC URL and Safe address."""
            try:
                ethereum_client = EthereumClient(rpc_url)
                safe_address = ChecksumAddress(safe_address)
                safe_instance = Safe(
                    address=safe_address, ethereum_client=ethereum_client
                )
                print_formatted_text(
                    HTML(
                        "\n<b><green>Safe instance initialized successfully!</green></b>\n"
                    )
                )
                return safe_instance
            except Exception as e:
                logger.error(f"Failed to initialize Safe instance: {e}")
                return None

        # If RPC URL and Safe address are provided, try to initialize the Safe instance
        if rpc_url and safe_address:
            safe_instance = _try_initialize_safe_instance(rpc_url, safe_address)

        # If that failed, or values are missing, prompt interactively
        while not safe_instance:
            try:
                if not rpc_url:
                    rpc_url = prompt_session.prompt(
                        HTML("<orange>#init Safe ></orange> Enter RPC URL: "),
                        validator=validator_rpc_url,
                        placeholder=HTML(
                            "<grey>e.g. https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID</grey>"
                        ),
                    )
                if not safe_address:
                    safe_address = prompt_session.prompt(
                        HTML("<orange>#init_safe ></orange> Enter Safe address: "),
                        validator=validator_address,
                        placeholder=HTML(
                            "<grey>e.g. 0x1234567890abcdef1234567890abcdef12345678</grey>"
                        ),
                    )
                safe_instance = _try_initialize_safe_instance(rpc_url, safe_address)
                if not safe_instance:
                    # Reset values to force re-prompt
                    rpc_url = None
                    safe_address = None
            except KeyboardInterrupt:
                logger.info("Exiting initialization.")
                return 0
            except Exception as e:
                logger.error(f"An error occurred: {e}")
                return 1

        # Start the interactive session for multisig transactions
        print_formatted_text(
            HTML(
                "\n<b><magenta>Starting interactive transaction builder session...</magenta></b>\n"
            )
        )
        while True:
            try:
                # Prompt for SafeTx parameters
                if not safe_nonce:
                    safe_nonce = prompt_session.prompt(
                        HTML("<orange>#tx_builder ></orange> Enter Safe nonce: "),
                        validator=validator_number,
                        placeholder=HTML("<grey>[default: auto retrieval]</grey>"),
                    )
                    if safe_nonce:
                        safe_nonce = int(safe_nonce)
                    else:
                        # Automatically retrieve nonce from Safe instance
                        safe_nonce = safe_instance.retrieve_nonce()
                if not gas_token:
                    gas_token = prompt_session.prompt(
                        HTML(
                            "<orange>#tx_builder ></orange> Enter gas token address (or press Enter to use ZERO_ADDRESS): "
                        ),
                        validator=validator_address,
                        placeholder=HTML("<grey>[default: 0x...]</grey>"),
                    )
                    if gas_token:
                        gas_token = ChecksumAddress(gas_token)
                    else:
                        gas_token = to_checksum_address(ZERO_ADDRESS)

                # If no data is provided, build the transaction(s) in a single loop and encode with MultiSend if needed
                if not data:
                    internal_txs = []
                    nb_internal_txs = prompt_session.prompt(
                        HTML(
                            "<orange>#tx_builder ></orange> Enter number of internal transactions: "
                        ),
                        validator=validator_not_zero_number,
                        placeholder=HTML("<grey>[default: 1]</grey>"),
                    )
                    if nb_internal_txs:
                        nb_internal_txs = int(nb_internal_txs)
                    else:
                        nb_internal_txs = 1

                    for idx in range(nb_internal_txs):
                        print_formatted_text(
                            HTML(
                                f"\n\t<b><magenta>--- Transaction {str(idx + 1).zfill(2)}/{str(nb_internal_txs).zfill(2)} ---</magenta></b>\n"
                            )
                        )
                        tx_type = prompt_session.prompt(
                            HTML(
                                "<orange>#tx_builder:internal_txs ></orange> Type of transaction (0 for call_contract, 1 for erc20_transfer, 2 for raw): "
                            ),
                            validator=validator_transaction_type,
                            placeholder=HTML(
                                "<grey>[default: 0 for call_contract]</grey>"
                            ),
                        )
                        if tx_type:
                            tx_type = int(tx_type)
                        else:
                            tx_type = 0

                        tx_to = ChecksumAddress(ZERO_ADDRESS)
                        tx_value = 0
                        tx_data = b""
                        tx_operation = 0

                        # Handle CALL contract transaction
                        if tx_type == 0:
                            # Prompt for contract address
                            tx_to = prompt_session.prompt(
                                HTML(
                                    "<orange>#tx_builder:internal_txs ></orange> Contract address: "
                                ),
                                validator=validator_address,
                                placeholder=HTML("<grey>[default: 0x...]</grey>"),
                            )
                            if tx_to:
                                tx_to = ChecksumAddress(tx_to)
                            else:
                                tx_to = to_checksum_address(ZERO_ADDRESS)

                            # Prompt for value
                            tx_value = prompt_session.prompt(
                                HTML(
                                    "<orange>#tx_builder:internal_txs ></orange> Value in wei: "
                                ),
                                validator=validator_number,
                                placeholder=HTML("<grey>[default: 0]</grey>"),
                            )
                            if tx_value:
                                tx_value = int(tx_value)
                            else:
                                tx_value = 0

                            # Prompt for operation type
                            tx_operation = prompt_session.prompt(
                                HTML(
                                    "<orange>#tx_builder:internal_txs ></orange> Operation type (0 for call, 1 for delegate call): "
                                ),
                                validator=validator_operation,
                                placeholder=HTML("<grey>[default: 0 for call]</grey>"),
                            )
                            if tx_operation:
                                tx_operation = int(tx_operation)
                            else:
                                tx_operation = 0

                            # Prompt for function signature
                            function_signature: str = prompt_session.prompt(
                                HTML(
                                    "<orange>#tx_builder:internal_txs ></orange> Function signature: "
                                ),
                                validator=validator_function_signature,
                                placeholder=HTML(
                                    "<grey>e.g. transfer(address,uint256)</grey>"
                                ),
                            )
                            func_name, params = function_signature.strip().split("(")
                            param_types = (
                                params.rstrip(")").split(",")
                                if params.rstrip(")")
                                else []
                            )

                            param_values = []
                            for i, typ in enumerate(param_types):
                                validator = param_type_validators.get(
                                    typ, validator_not_empty
                                )
                                val: str = prompt_session.prompt(
                                    HTML(
                                        f"<yellow>#tx_builder:internal_txs ></yellow> Parameter #{i + 1} ({typ}): "
                                    ),
                                    validator=validator,
                                )
                                param_values.append(val)
                            # Import eth_abi.abi.encode for ABI encoding
                            from eth_abi.abi import encode as abi_encode
                            from eth_utils import function_signature_to_4byte_selector

                            # Convert param_values to correct types for eth_abi
                            def parse_value(val, typ):
                                # Basic support for common types
                                if typ.startswith("uint") or typ.startswith("int"):
                                    return int(val)
                                if typ == "address":
                                    return val if val.startswith("0x") else "0x" + val
                                if typ == "bool":
                                    return val.lower() in ("true", "1", "yes")
                                if typ.startswith("bytes"):
                                    from eth_utils import to_bytes

                                    return to_bytes(hexstr=val)
                                return val

                            parsed_param_values = [
                                parse_value(v, t)
                                for v, t in zip(param_values, param_types)
                            ]
                            selector = function_signature_to_4byte_selector(
                                f"{func_name}({','.join(param_types)})"
                            )
                            encoded_args = abi_encode(param_types, parsed_param_values)
                            tx_data = selector + encoded_args

                        # @TODO: Handle ERC20 transfer
                        # elif tx_type == 1:
                        #     pass

                        # Handle raw transaction
                        elif tx_type == 2:
                            tx_data_hex = prompt_session.prompt(
                                HTML(
                                    "<orange>#tx_builder:internal_txs ></orange> Raw data (hex): "
                                ),
                                validator=validator_data,
                                placeholder=HTML("<grey>e.g. 0x...</grey>"),
                            )
                            tx_data = to_bytes(hexstr=tx_data_hex)

                        # Build MultiSendTx directly
                        internal_txs.append(
                            MultiSendTx(
                                operation=MultiSendOperation(tx_operation),
                                to=tx_to,
                                value=int(tx_value),
                                data=tx_data,
                            )
                        )

                    # If more than one internal tx, use MultiSend
                    if len(internal_txs) > 1:
                        multi_send = MultiSend(ethereum_client=EthereumClient(rpc_url))
                        data = multi_send.build_tx_data(internal_txs)
                        to = multi_send.address
                        value = 0
                        operation = 0

                    elif len(internal_txs) == 1:
                        # Single tx, use as is
                        tx = internal_txs[0]
                        to = tx.to
                        value = tx.value
                        data = tx.data
                        operation = tx.operation.value

                print_formatted_text(
                    HTML(
                        "\n<b><green>MultiSend transaction created successfully!</green></b>\n"
                    )
                )

                # --- MultiSend batch detection and 'to' override logic ---
                if data:
                    try:
                        decoded_batch = MultiSend.from_transaction_data(data)
                    except Exception as e:
                        decoded_batch = []
                        logger.warning(f"Could not decode data as MultiSend batch: {e}")

                    # If decoded batch is found, override 'to' with MultiSend address
                    if decoded_batch:
                        # Check if it contains delegate calls
                        has_delegate = any(
                            tx.operation == MultiSendOperation.DELEGATE_CALL
                            for tx in decoded_batch
                        )
                        multi_send = MultiSend(
                            ethereum_client=EthereumClient(rpc_url),
                            call_only=not has_delegate,
                        )
                        multi_send_address = multi_send.address

                        # Override 'to' if provided or if it was not set
                        if to and to != multi_send_address:
                            print_formatted_text(
                                HTML(
                                    f"<b><yellow>Warning:</yellow></b> Overriding provided --to address with MultiSend address: {multi_send_address}"
                                )
                            )
                        to = multi_send_address

                        # Show decoded batch to user for confirmation
                        print_formatted_text(
                            HTML("<b><magenta>Decoded MultiSend batch:</magenta></b>")
                        )
                        for idx, tx in enumerate(decoded_batch, 1):
                            print_formatted_text(
                                HTML(
                                    f"<b>Tx {idx}:</b> "
                                    f"operation={tx.operation.name}, "
                                    f"to={tx.to}, "
                                    f"value={tx.value}, "
                                    f"data={tx.data.hex()[:20]}{'...' if len(tx.data) > 10 else ''}"
                                )
                            )
                        confirm = prompt_session.prompt(
                            HTML(
                                "<orange>Does this batch look correct? (y/n): </orange>"
                            ),
                            placeholder="y/n, yes/no",
                        )
                        if confirm.lower() not in ("y", "yes"):
                            print_formatted_text(
                                HTML(
                                    "<b><red>Aborting due to user rejection of decoded batch.</red></b>"
                                )
                            )
                            return 1

                    # Not a MultiSend batch, prompt for 'to'
                    elif not to:
                        to = prompt_session.prompt(
                            HTML(
                                "<orange>#tx_builder ></orange> Enter target contract address (to): "
                            ),
                            validator=validator_address,
                            placeholder=HTML("<grey>e.g. 0x...</grey>"),
                        )
                        to = ChecksumAddress(to)

                # Create the SafeTx instance
                try:
                    safe_tx = safe_instance.build_multisig_tx(
                        to=to,
                        value=value,
                        operation=operation,
                        safe_nonce=safe_nonce,
                        data=data,
                        gas_token=gas_token,
                    )
                    # Print the SafeTx instance
                    prompt_clear()
                    print_formatted_text(
                        HTML(
                            "\n<b><green>SafeTx instance created successfully!</green></b>\n"
                        )
                    )
                    # Pretty-print SafeTx fields
                    from safe_eth.util.util import to_0x_hex_str

                    print_formatted_text(HTML("<b>SafeTx</b>"))
                    print_formatted_text(
                        HTML(
                            f"\t<b><orange>Safe Address:</orange></b> {safe_tx.safe_address}"
                        )
                    )
                    print_formatted_text(
                        HTML(
                            f"\t<b><orange>Safe Nonce:</orange></b> {safe_tx.safe_nonce}"
                        )
                    )
                    print_formatted_text(
                        HTML(
                            f"\t<b><orange>Safe Version:</orange></b> {safe_tx.safe_version}\n"
                        )
                    )
                    print_formatted_text(
                        HTML(f"\t<b><orange>To:</orange></b> {safe_tx.to}")
                    )
                    print_formatted_text(
                        HTML(f"\t<b><orange>Value:</orange></b> {safe_tx.value}")
                    )
                    print_formatted_text(
                        HTML(
                            f"\t<b><orange>Data:</orange></b> {to_0x_hex_str(safe_tx.data)}"
                        )
                    )
                    print_formatted_text(
                        HTML(
                            f"\t<b><orange>Operation:</orange></b> {safe_tx.operation}"
                        )
                    )
                    print_formatted_text(
                        HTML(
                            f"\t<b><orange>SafeTx Gas:</orange></b> {safe_tx.safe_tx_gas}"
                        )
                    )
                    print_formatted_text(
                        HTML(f"\t<b><orange>Base Gas:</orange></b> {safe_tx.base_gas}")
                    )
                    print_formatted_text(
                        HTML(
                            f"\t<b><orange>Gas Price:</orange></b> {safe_tx.gas_price}"
                        )
                    )
                    print_formatted_text(
                        HTML(
                            f"\t<b><orange>Gas Token:</orange></b> {safe_tx.gas_token}"
                        )
                    )
                    print_formatted_text(
                        HTML(
                            f"\t<b><orange>Refund Receiver:</orange></b> {safe_tx.refund_receiver}"
                        )
                    )
                    print_formatted_text(
                        HTML(f"\t<b><orange>Signers:</orange></b> {safe_tx.signers}")
                    )
                    print_formatted_text(
                        HTML(f"\t<b><orange>Chain ID:</orange></b> {safe_tx.chain_id}")
                    )
                    # Break the loop after successful creation
                    break
                except Exception as e:
                    logger.error(f"Failed to create SafeTx instance: {e}")
                break

            except KeyboardInterrupt:
                logger.info("Exiting interactive mode.")
                break
            except Exception as e:
                logger.error(f"An error occurred: {e}")
                return 1

    # Unknown command handling
    else:
        logger.warning(f"Unknown msig command: {args.msig_command}")
    return 0
