from argparse import Namespace
from moccasin.logging import logger
from eth_utils import is_address
from eth.constants import ZERO_ADDRESS
from eth_typing import Address
from eth_abi.grammar import parse as parse_abi_signature
from eth_abi.exceptions import ParseError
from constants.vars import DEFAULT_NETWORKS_BY_CHAIN_ID


def main(args: Namespace) -> int:
    if args.msig_command == "tx":
        tx_builder(args)
    else:
        logger.warning(f"Unknown msig command: {args.msig_command}")
    return 0


def tx_builder(args: Namespace):
    chain_id: int = 1
    safe_address: Address = ZERO_ADDRESS
    num_txs: int = 1
    data: bytes = b""
    gas_token: Address = ZERO_ADDRESS
    refund_receiver: Address = ZERO_ADDRESS
    nonce: int | None = None

    if args.interactive:
        print(
            bold(cyan("\n✨ Welcome to Moccasin msig tx builder interactive mode! ✨"))
        )
        print(yellow("Press Enter to begin!"))
        input()

        # Step 1: Chain ID
        print(bold("\n🌐 Step 1: Network Selection"))
        while True:
            try:
                chain_id_input = input(
                    green(
                        "Enter Chain ID (e.g., 1 for Mainnet, 42161 for Arbitrum...) [default: 1]: "
                    )
                ).strip()
                if chain_id_input.isdigit():
                    chain_id = int(chain_id_input)
                    if chain_id in DEFAULT_NETWORKS_BY_CHAIN_ID:
                        break
                    else:
                        print(
                            yellow(
                                "Unsupported Chain ID. Please enter a valid Chain ID."
                            )
                        )
                else:
                    print(yellow("Invalid input. Please enter a number."))
            except ValueError:
                print(yellow("Invalid input. Please enter a number."))

        # Step 2: Safe Address
        print(bold("\n🔒 Step 2: Safe Address"))
        while True:
            safe_address_input = input(
                green("Enter the Gnosis Safe multisig address [default: 0x00...00]: ")
            ).strip()
            if is_address(safe_address_input):
                safe_address = safe_address_input
                break
            else:
                print(yellow("Invalid address format. Please try again."))

        # Step 3: Number of Transactions
        print(bold("\n📝 Step 3: Internal Transactions"))
        while True:
            try:
                num_txs = int(
                    input(
                        green("How many internal transactions to batch [default: 1]? ")
                    ).strip()
                )
                if num_txs > 0:
                    break
                else:
                    print(yellow("Please enter a positive integer."))
            except ValueError:
                print(yellow("Invalid input. Please enter a number."))

        # Internal transactions input loop
        internal_txs = []
        for i in range(num_txs):
            print(bold(magenta(f"\n--- Internal Transaction {i + 1} of {num_txs} ---")))
            tx_type = (
                input(green("Type of transaction ([contract_call]/ether_transfer): "))
                .strip()
                .lower()
                or "contract_call"
            )
            contract_address = None
            function_signature = None
            function_params = None
            if tx_type == "contract_call":
                while True:
                    contract_address_input = input(green("Contract address: ")).strip()
                    if is_address(contract_address_input):
                        contract_address = contract_address_input
                        break
                    else:
                        print(yellow("Invalid address format. Please try again."))

                # Function signature
                while True:
                    function_signature_input = input(
                        green("Function signature (e.g., transfer(address,uint256)): ")
                    ).strip()
                    if is_valid_function_signature(function_signature_input):
                        function_signature = function_signature_input
                        break
                    else:
                        print(
                            yellow(
                                "Invalid function signature. Please enter a valid signature."
                            )
                        )
                # Function parameters
                # @TODO: Implement type-checking for function parameters
                function_params = input(
                    green("Function parameters (comma-separated, type-checked): ")
                ).strip()

            # Ether to transfer
            value = input(green("Value (ETH) to send with this transaction: ")).strip()

            # Operation type selection: 0 for CALL, 1 for DELEGATE_CALL
            while True:
                op_input = input(
                    green(
                        "Operation type ([0] CALL / [1] DELEGATE_CALL) [default: 0]: "
                    )
                ).strip()
                if op_input == "":
                    operation_type = 0
                    break
                elif op_input in ("0", "1"):
                    operation_type = int(op_input)
                    break
                else:
                    print(
                        yellow(
                            "Invalid input. Please enter 0 for CALL or 1 for DELEGATE_CALL."
                        )
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
        print(bold("\n⛽ Step 4: Gas Token"))
        gas_token = (
            input(
                green("Gas token address (ERC-20 or 0x00...00 for native token): ")
            ).strip()
            or ZERO_ADDRESS
        )

        # Step 5: Refund Receiver
        print(bold("\n🎁 Step 5: Refund Receiver"))
        refund_receiver = (
            input(green("Refund receiver address: ")).strip() or ZERO_ADDRESS
        )

        # Step 6: Nonce
        print(bold("\n🔢 Step 6: Nonce"))
        nonce = input(green("Nonce (leave blank to auto-fetch): ")).strip()
        # @TODO: Implement nonce auto-fetch logic

        # Summary
        print(bold(cyan("\n📋 Transaction Summary:")))
        print(f"{bold('Chain ID:')} {chain_id}")
        print(f"{bold('Safe Address:')} {safe_address}")
        print(f"{bold('Number of internal transactions:')} {num_txs}")
        for idx, tx in enumerate(internal_txs, 1):
            print(magenta(f"\n  ── Tx {idx} ──────────────"))
            print(f"    {bold('Type:')} {tx['type']}")
            if tx["type"] == "contract_call":
                print(f"\t{bold('Contract Address:')} {tx['contract_address']}")
                print(f"\t{bold('Function Signature:')} {tx['function_signature']}")
                print(f"\t{bold('Function Params:')} {tx['function_params']}")
            print(f"\t{bold('Value (ETH):')} {tx['value']}")
            print(f"\t{bold('Operation Type:')} {tx['operation_type']}")
        print(f"\n{bold('Gas Token:')} {gas_token}")
        print(f"{bold('Refund Receiver:')} {refund_receiver}")
        print(f"{bold('Nonce:')} {nonce if nonce else '[auto-fetch]'}")

        print(bold(green("\n✅ Interactive input complete!")))
        print(
            yellow(
                "Transaction creation/submission not yet implemented. Thank you for using Moccasin!"
            )
        )
        return 0
    else:
        logger.warning(
            "Interactive mode is not enabled. WIP for non-interactive mode. Use --interactive to enable it."
        )
        return 1


# Utility function to check if a function signature is valid
def is_valid_function_signature(signature: str) -> bool:
    """Checks if a string is a valid human-readable function signature.

    `eth_abi.grammar.parse` can parse various ABI fragment types.
    For a function, it expects something like "function foo(uint256 a, address b) returns (bool)".
    However, for simply validating the signature part, you often only need the name and parameters.
    """
    try:
        # If the signature doesn't start with "function ", add it for robust parsing.
        if not signature.strip().startswith("function "):
            test_signature = f"function {signature.strip()}"
        else:
            test_signature = signature.strip()

        # This will raise a ParseError if the signature is malformed
        parse_abi_signature(test_signature)

        # If it parses without error and is a function, it's valid
        return True
    except ParseError as e:
        print(f"Invalid function signature: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


# Simple color helpers
def color(text, code):
    return f"\033[{code}m{text}\033[0m"


def bold(text):
    return color(text, "1")


def cyan(text):
    return color(text, "36")


def green(text):
    return color(text, "32")


def yellow(text):
    return color(text, "33")


def magenta(text):
    return color(text, "35")
