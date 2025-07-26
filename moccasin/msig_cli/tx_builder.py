from argparse import Namespace
from moccasin.logging import logger
from eth_utils import to_checksum_address, to_bytes
from eth.constants import ZERO_ADDRESS
from eth_typing import ChecksumAddress
from eth_abi.grammar import parse as parse_abi_signature
from eth_abi.exceptions import ParseError, ABITypeError
from constants.vars import DEFAULT_NETWORKS_BY_CHAIN_ID


"""
    @TODO - Rework custom tx builder from AI promts with:
    - https://github.dev/safe-global/safe-cli/blob/main/src/safe_cli implementation
    - Need to use argparse `type=` to double check user input with internal validation to use it interactively
    - Use enum from our vars.py
    - Might need Web3.py for more complex interactions and Nonce management -> maybe add safe-eth-py package since it has it?
    - Use prompt-toolkit (already a dependency in moccasin) for better CLI experience as Safe CLI does

    @dev Goal -> Same tx builder as Safer Morpho, but we need Safe CLI robustness and features without importing the whole Safe CLI package.
    @dev Note -> This is a WIP, not yet functional. Use --interactive to
"""


def main(args: Namespace):
    chain_id: int = 1
    safe_address: ChecksumAddress = to_checksum_address(ZERO_ADDRESS)
    num_txs: int = 1
    data: bytes = b""
    gas_token: ChecksumAddress = to_checksum_address(ZERO_ADDRESS)
    refund_receiver: ChecksumAddress = to_checksum_address(ZERO_ADDRESS)
    nonce: int | None = None

    if args.interactive:
        print("\n✨ Welcome to Moccasin msig tx builder interactive mode! ✨")
        print("Press Enter to begin!")
        input()

        # Step 1: Chain ID
        print("\n🌐 Step 1: Network Selection")
        while True:
            try:
                chain_id_input = input(
                    "Enter Chain ID (e.g., 1 for Mainnet, 42161 for Arbitrum...) [default: 1]: "
                ).strip()
                if chain_id_input.isdigit():
                    chain_id = int(chain_id_input)
                    if chain_id in DEFAULT_NETWORKS_BY_CHAIN_ID:
                        break
                    else:
                        print("Unsupported Chain ID. Please enter a valid Chain ID.")
                else:
                    print("Invalid input. Please enter a number.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        # Step 2: Safe Address
        print("\n🔒 Step 2: Safe Address")
        while True:
            safe_address_input = input(
                "Enter the Gnosis Safe multisig address [default: 0x00...00]: "
            ).strip()
            try:
                safe_address_input = to_checksum_address(safe_address_input)
                break
            except Exception:
                print("Invalid address format. Please try again.")

        # Step 3: Number of Transactions
        print("\n📝 Step 3: Internal Transactions")
        while True:
            try:
                num_txs = int(
                    input(
                        "How many internal transactions to batch [default: 1]? "
                    ).strip()
                )
                if num_txs > 0:
                    break
                else:
                    print("Please enter a positive integer.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        # Internal transactions input loop
        internal_txs = []
        for i in range(num_txs):
            print(f"\n--- Internal Transaction {i + 1} of {num_txs} ---")
            tx_type = (
                input("Type of transaction ([contract_call]/ether_transfer): ")
                .strip()
                .lower()
                or "contract_call"
            )
            contract_address = None
            function_signature = None
            function_params = None
            if tx_type == "contract_call":
                while True:
                    contract_address_input = input("Contract address: ").strip()
                    try:
                        contract_address = to_checksum_address(contract_address_input)
                        break
                    except Exception:
                        print(
                            "Invalid contract address format. Please enter a valid address."
                        )

                # Function signature
                while True:
                    function_signature_input = input(
                        "Function signature (e.g., transfer(address,uint256)): "
                    ).strip()
                    if is_valid_function_signature(function_signature_input):
                        function_signature = function_signature_input
                        break
                    else:
                        print(
                            "Invalid function signature. Please enter a valid signature."
                        )
                # Function parameters
                # @TODO: Implement type-checking for function parameters
                function_params = input(
                    "Function parameters (comma-separated, type-checked): "
                ).strip()

            # Ether to transfer
            value = input("Value (ETH) to send with this transaction: ").strip()

            # Operation type selection: 0 for CALL, 1 for DELEGATE_CALL
            while True:
                op_input = input(
                    "Operation type ([0] CALL / [1] DELEGATE_CALL) [default: 0]: "
                ).strip()
                if op_input == "":
                    operation_type = 0
                    break
                elif op_input in ("0", "1"):
                    operation_type = int(op_input)
                    break
                else:
                    print(
                        "Invalid input. Please enter 0 for CALL or 1 for DELEGATE_CALL."
                    )

            internal_txs.append(
                {
                    "type": tx_type,
                    "contract_address": contract_address,
                    "function_signature": function_signature,
                    "function_params": function_params,
                    "value": value,
                    "operation_type": operation_type,
                }
            )

        # Step 4: Gas Token
        print("\n⛽ Step 4: Gas Token")
        while True:
            gas_token = input(
                "Gas token address (ERC-20 or 0x00...00 for native token): "
            ).strip() or to_checksum_address(ZERO_ADDRESS)
            try:
                gas_token = to_checksum_address(gas_token)
                break
            except Exception:
                print("Invalid gas token address format. Please enter a valid address.")

        # Step 5: Refund Receiver
        print("\n🎁 Step 5: Refund Receiver")
        while True:
            try:
                refund_receiver = input(
                    "Refund receiver address: "
                ).strip() or to_checksum_address(ZERO_ADDRESS)
                refund_receiver = to_checksum_address(refund_receiver)
                break
            except Exception:
                print(
                    "Invalid refund receiver address format. Please enter a valid address."
                )

        # Step 6: Nonce
        print("\n🔢 Step 6: Nonce")
        while True:
            nonce_input = input("Nonce (leave blank to auto-fetch): ").strip()
            if nonce_input.isdigit():
                nonce = int(nonce_input)
                break
            elif nonce_input == "":
                nonce = 0  # @dev default 0 for now
                break
                # @TODO: Implement nonce auto-fetch logic
            else:
                print(
                    "Invalid nonce input. Please enter a number or leave blank for auto-fetch."
                )
                nonce = None

        # Summary
        print("\n📋 Transaction Summary:")
        print(f"Chain ID: {chain_id}")
        print(f"Safe Address: {safe_address}")
        print(f"Number of internal transactions: {num_txs}")
        for idx, tx in enumerate(internal_txs, 1):
            print(f"\n  ── Tx {idx} ──────────────")
            print(f"    Type: {tx['type']}")
            if tx["type"] == "contract_call":
                print(f"\tContract Address: {tx['contract_address']}")
                print(f"\tFunction Signature: {tx['function_signature']}")
                print(f"\tFunction Params: {tx['function_params']}")
            print(f"\tValue (ETH): {tx['value']}")
            print(f"\tOperation Type: {tx['operation_type']}")
        print(f"\nGas Token: {gas_token}")
        print(f"Refund Receiver: {refund_receiver}")
        print(f"Nonce: {nonce if nonce else '[auto-fetch]'}")

        print("\n✅ Interactive input complete!")
        print(
            "Transaction creation/submission not yet implemented. Thank you for using Moccasin!"
        )
        return 0
    else:
        logger.warning(
            "Interactive mode is not enabled. WIP for non-interactive mode. Use --interactive to enable it."
        )
        return 1


# Utility function to check if a function signature is valid
def is_valid_function_signature(signature_str: str) -> tuple[bool, list]:
    """
    Checks if a string is a valid human-readable function signature
    and extracts its input types if valid.

    Returns:
        tuple: (is_valid: bool, input_types: list[str] or None)
    """
    try:
        if not signature_str.strip().startswith("function "):
            test_signature = f"function {signature_str.strip()}"
        else:
            test_signature = signature_str.strip()

        parsed_fragment = parse_abi_signature(test_signature)

        if (
            parsed_fragment.is_constructor
            or parsed_fragment.is_event
            or parsed_fragment.is_error
        ):
            # It parsed, but it's not a function.
            return False, None

        # Extract parameter types
        input_types = [param.canonical_type for param in parsed_fragment.inputs]
        return True, input_types
    except ParseError as e:
        logger.debug(f"Invalid function signature format: {e}")
        return False, None
    except Exception as e:
        logger.debug(f"An unexpected error occurred during signature parsing: {e}")
        return False, None


def validate_function_params(
    input_params_str: str, expected_types: list[str]
) -> tuple[bool, list, str]:
    """
    Validates a comma-separated string of parameters against a list of expected ABI types.

    Args:
        input_params_str: A string like "0xabc...,123," for parameters.
        expected_types: A list of canonical ABI type strings (e.g., ['address', 'uint256']).

    Returns:
        tuple: (is_valid: bool, converted_params: list, error_message: str)
    """
    if not input_params_str:
        user_params = []
    else:
        # Basic splitting, assumes no commas within parameters (e.g., in nested tuples)
        # For more complex parsing of nested structures, you might need a more sophisticated parser.
        user_params_raw = [p.strip() for p in input_params_str.split(",")]
        # Filter out empty strings that result from trailing commas or multiple commas
        user_params = [p for p in user_params_raw if p]

    if len(user_params) != len(expected_types):
        return (
            False,
            [],
            f"Number of parameters mismatch. Expected {len(expected_types)}, got {len(user_params)}.",
        )

    converted_params = []
    for i, (param_raw, expected_type) in enumerate(zip(user_params, expected_types)):
        try:
            if expected_type == "address":
                converted_params.append(to_checksum_address(param_raw))
            elif expected_type.startswith("uint") or expected_type.startswith("int"):
                # Handle integers. Python's int conversion handles most cases.
                converted_params.append(int(param_raw))
                # Optional: Add range check for uint/int if strictness is needed (e.g., uint8 max 255)
            elif expected_type == "bool":
                if param_raw.lower() in ["true", "1"]:
                    converted_params.append(True)
                elif param_raw.lower() in ["false", "0"]:
                    converted_params.append(False)
                else:
                    raise ValueError(
                        f"Invalid boolean value for type '{expected_type}': '{param_raw}'"
                    )
            elif expected_type.startswith("bytes"):
                # bytesN (fixed size) or bytes (dynamic)
                if param_raw.startswith("0x"):  # Assume hex string input for bytes
                    converted_params.append(to_bytes(param_raw))
                else:  # Try as regular string and encode
                    converted_params.append(
                        param_raw.encode("utf-8")
                    )  # Or another encoding if required
            elif expected_type == "string":
                converted_params.append(
                    param_raw
                )  # Python strings are fine for ABI strings

            # @TODO @dev: Handle more complex types like arrays, tuples, etc.
            # Add more specific type handling (e.g., arrays, tuples) as needed
            # For arrays, you'd need to parse the array syntax (e.g., 'uint256[]')
            # and then recursively validate elements.
            # For tuples, you'd need to parse the tuple syntax and its components.
            else:
                # For types not explicitly handled, assume simple string conversion or try direct casting
                # This might not always be perfectly accurate for complex ABI types.
                # For robust handling of all ABI types, you would integrate more deeply with eth-abi.
                converted_params.append(
                    param_raw
                )  # Fallback, might need specific type mapping
                logger.debug(
                    f"Warning: No specific handling for type '{expected_type}'. Using raw input."
                )

        except ValueError as e:
            return (
                False,
                [],
                f"Parameter {i + 1} ('{param_raw}') does not match expected type '{expected_type}': {e}",
            )
        except ABITypeError as e:
            return (
                False,
                [],
                f"Parameter {i + 1} ('{param_raw}') has an ABI type error for '{expected_type}': {e}",
            )
        except Exception as e:
            return (
                False,
                [],
                f"An unexpected error occurred processing parameter {i + 1} ('{param_raw}') for type '{expected_type}': {e}",
            )

    return True, converted_params, "Parameters valid."


# --- Your combined input loop ---
def get_function_and_params():
    function_signature = None
    input_types = None
    function_params = None

    # Function signature loop
    while True:
        function_signature_input = input(
            "Function signature (e.g., transfer(address,uint256)): "
        ).strip()

        is_sig_valid, types = is_valid_function_signature(function_signature_input)
        if is_sig_valid:
            function_signature = function_signature_input
            input_types = types
            print(
                f"Signature valid. Expected parameter types: {', '.join(input_types)}"
            )
            break
        else:
            print("Invalid function signature. Please enter a valid signature.")

    # Function parameters loop
    while True:
        params_input = input(
            "Function parameters (comma-separated, e.g., 0x...,123): "
        ).strip()

        is_params_valid, converted_params, error_msg = validate_function_params(
            params_input, input_types
        )

        if is_params_valid:
            function_params = converted_params
            print("Parameters successfully parsed and type-checked!")
            print(f"Parsed parameters: {function_params}")
            break
        else:
            print(f"Invalid parameters: {error_msg}")
            print("Please re-enter parameters matching the signature.")

    return function_signature, function_params
