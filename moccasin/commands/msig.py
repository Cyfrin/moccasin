from argparse import Namespace
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address
from eth.constants import ZERO_ADDRESS

from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from moccasin.logging import logger

from safe_eth.eth import EthereumClient
from safe_eth.safe import Safe

from web3 import Web3


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
        safe_nonce: int = getattr(args, "nonce", 0)
        data: bytes = getattr(args, "data", b"")
        gas_token: ChecksumAddress = getattr(
            args, "gas_token", to_checksum_address(ZERO_ADDRESS)
        )

        # Check if interactive mode is enabled
        if args.interactive:
            # Create a prompt session with auto-suggest and a bottom toolbar
            prompt_session = PromptSession(
                auto_suggest=AutoSuggestFromHistory(),
                bottom_toolbar="Tips: Use Ctrl-C to exit.",
            )

            # Intitialize Safe instance
            print_formatted_text(
                HTML("<b><orange>Initializing Safe instance...</orange></b>")
            )
            # Prompt for RPC URL and Safe address if not provided
            if not rpc_url or not safe_address:
                while True:
                    try:
                        if not rpc_url:
                            rpc_url = prompt_session.prompt(
                                "#init Safe > Enter RPC URL: "
                            )
                        if not safe_address:
                            safe_address = prompt_session.prompt(
                                "#init_safe > Enter Safe address: "
                            )
                        if rpc_url and safe_address:
                            # Create a Safe instance with the provided RPC URL and address
                            try:
                                # Set Ethereum client URL and Safe address
                                rpc_url = (
                                    rpc_url.strip()
                                )  # public https://sepolia.drpc.org
                                ethereum_client = EthereumClient(rpc_url)
                                safe_address = ChecksumAddress(safe_address.strip())

                                safe_instance = Safe(
                                    address=safe_address,
                                    ethereum_client=ethereum_client,
                                )
                                # If the Safe instance is initialized successfully, break the loop
                                if safe_instance:
                                    print_formatted_text(
                                        HTML(
                                            "<b><green>Safe instance initialized successfully!</green></b>"
                                        )
                                    )
                                    break
                                else:
                                    logger.error("Failed to initialize Safe instance.")
                                    rpc_url = None
                                    safe_address = None
                                    continue
                            # If initialization fails, log the error and prompt again
                            except Exception as e:
                                logger.error(f"Failed to initialize Safe instance: {e}")
                                continue
                    except KeyboardInterrupt:
                        logger.info("Exiting initialization.")
                        return 0
                    except Exception as e:
                        logger.error(f"An error occurred: {e}")
                        continue

            # Start the interactive session for multisig transactions
            print_formatted_text(
                HTML(
                    "<b><orange>Starting interactive transaction builder session...</orange></b>"
                )
            )
            while True:
                try:
                    # Prompt for SafeTx parameters
                    if not to:
                        to = prompt_session.prompt(
                            "#tx_builder > Enter 'to' address (or press Enter to use ZERO_ADDRESS): "
                        )
                        if to:
                            to = ChecksumAddress(to.strip())
                        else:
                            to = to_checksum_address(ZERO_ADDRESS)

                    if not value:
                        value = prompt_session.prompt(
                            "#tx_builder > Enter value in wei (or press Enter to use 0): "
                        )
                        if value:
                            value = int(value)
                        else:
                            value = 0

                    if not operation:
                        operation = prompt_session.prompt(
                            "#tx_builder > Enter operation (0 for call [default], 1 for delegate call): "
                        )
                        if operation:
                            operation = int(operation)
                        else:
                            operation = 0
                    # @FIXME: Initialize Safe nonce if not provided
                    if not safe_nonce:
                        safe_nonce = prompt_session.prompt(
                            "#tx_builder > Enter Safe nonce (or press Enter to set it automatically): "
                        )
                        if safe_nonce:
                            safe_nonce = int(safe_nonce)
                        else:
                            # Automatically retrieve nonce from Safe instance
                            safe_instance.retrieve_nonce()
                    if not gas_token:
                        gas_token = prompt_session.prompt(
                            "#tx_builder > Enter gas token address (or press Enter to use ZERO_ADDRESS): "
                        )
                        if gas_token:
                            gas_token = ChecksumAddress(gas_token.strip())
                        else:
                            gas_token = to_checksum_address(ZERO_ADDRESS)

                    # @TODO: Test data encoding and finish it too
                    # # If no data is provided, build the transaction
                    # if not data:
                    #     # Check how many internal transactions to create
                    #     internal_txs_list = []
                    #     nb_internal_txs = prompt_session.prompt(
                    #         "#tx_builder > Enter number of internal transactions (or press Enter to set to 1): "
                    #     )
                    #     if nb_internal_txs:
                    #         nb_internal_txs = int(nb_internal_txs)
                    #     else:
                    #         nb_internal_txs = 1

                    #     # Build the transactions
                    #     for idx in range(nb_internal_txs):
                    #         print_formatted_text(
                    #             HTML(
                    #                 f"\n<b><magenta>--- Transaction {str(idx + 1).zfill(2)}/{str(nb_internal_txs).zfill(2)} ---</magenta></b>\n"
                    #             )
                    #         )

                    #         # Prompt for transaction type
                    #         tx_type = int(
                    #             prompt_session.prompt(
                    #                 "Type of transaction (0 for call_contract, 1 for erc20_transfer, 2 for raw): "
                    #             )
                    #         )
                    #         # Set default values
                    #         tx_to = ChecksumAddress(ZERO_ADDRESS)
                    #         tx_value = 0
                    #         tx_data = b""
                    #         tx_operation = 0

                    #         # Handle different transaction types
                    #         if tx_type == 0:
                    #             tx_to = prompt_session.prompt(
                    #                 "Contract address (or press Enter to use ZERO_ADDRESS): "
                    #             )
                    #             if tx_to:
                    #                 tx_to = ChecksumAddress(tx_to.strip())
                    #             else:
                    #                 tx_to = to_checksum_address(ZERO_ADDRESS)

                    #             tx_value = int(
                    #                 prompt_session.prompt(
                    #                     "Value in wei (or press Enter to use 0): "
                    #                 )
                    #                 or 0
                    #             )

                    #             function_signature: str = prompt_session.prompt(
                    #                 "Function signature (e.g. transfer(address,uint256)): "
                    #             )
                    #             # Parse function name and types
                    #             func_name, params = function_signature.strip().split(
                    #                 "("
                    #             )
                    #             param_types = (
                    #                 params.rstrip(")").split(",")
                    #                 if params.rstrip(")")
                    #                 else []
                    #             )
                    #             param_values = []
                    #             for i, typ in enumerate(param_types):
                    #                 val: str = prompt_session.prompt(
                    #                     f"Parameter #{i + 1} ({typ}): "
                    #                 )
                    #                 param_values.append(val)
                    #             # Encode calldata
                    #             w3 = Web3()
                    #             contract_func = w3.codec.encode(
                    #                 param_types, param_values
                    #             )
                    #             method_id = w3.keccak(
                    #                 text=f"{func_name}({','.join(param_types)})"
                    #             )[:4]
                    #             tx_data = "0x" + method_id.hex() + contract_func.hex()
                    #         # @TODO: Handle ERC20 transfer
                    #         # elif tx_type == "erc20_transfer":
                    #         #     # Example: ERC20 transfer(address,uint256)
                    #         #     # You can hardcode or prompt for function signature and params
                    #         #     pass
                    #         elif tx_type == "raw":
                    #             data = prompt_session.prompt("Raw data (hex): ").strip()

                    #         tx_operation = (
                    #             int(
                    #                 prompt_session.prompt(
                    #                     "Operation type (0 for call, 1 for delegate call): "
                    #                 )
                    #             )
                    #             or 0
                    #         )

                    #         internal_txs_list.append(
                    #             {
                    #                 "to": tx_to,
                    #                 "data": tx_data,
                    #                 "value": tx_value,
                    #                 "operation": tx_operation,  # or prompt for operation type
                    #             }
                    #         )

                except KeyboardInterrupt:
                    logger.info("Exiting interactive mode.")
                    break
                except Exception as e:
                    logger.error(f"An error occurred: {e}")

        else:
            logger.warning(
                "Interactive mode is not enabled. Use --interactive to enable it."
            )
    # Unknown command handling
    else:
        logger.warning(f"Unknown msig command: {args.msig_command}")
    return 0
