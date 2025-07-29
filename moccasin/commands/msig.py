from argparse import Namespace
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address, is_hex_address
from eth.constants import ZERO_ADDRESS

from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from moccasin.logging import logger

from safe_eth.eth import EthereumClient
from safe_eth.safe import Safe
from safe_eth.safe.multi_send import MultiSend, MultiSendTx, MultiSendOperation


# --- Core Validators ---
def is_valid_address(address: str) -> bool:
    """Check if the provided address is a valid address."""
    return is_hex_address(address)


def is_valid_rpc_url(rpc_url: str) -> bool:
    """Check if the provided RPC URL is valid."""
    return rpc_url.startswith("http://") or rpc_url.startswith("https://")


def is_valid_number(value: str) -> bool:
    """Check if the provided value is a valid number."""
    return value.isdigit()


def is_valid_operation(value: str) -> bool:
    """Check if the provided value is a valid operation type."""
    return value.isdigit() and int(value) in [op.value for op in MultiSendOperation]


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
        gas_token: ChecksumAddress = getattr(args, "gas_token", None)

        # Create a prompt session with auto-suggest and a bottom toolbar
        prompt_session = PromptSession(
            auto_suggest=AutoSuggestFromHistory(),
            bottom_toolbar="Tips: Use Ctrl-C to exit.",
            validate_while_typing=False,
        )

        # Intitialize Safe instance
        print_formatted_text(
            HTML("\n<b><magenta>Initializing Safe instance...</magenta></b>\n")
        )
        # Prompt for RPC URL and Safe address if not provided
        if not rpc_url or not safe_address:
            while True:
                try:
                    if not rpc_url:
                        rpc_url = prompt_session.prompt(
                            HTML("<orange>#init Safe ></orange> Enter RPC URL: ")
                        )
                    if not safe_address:
                        safe_address = prompt_session.prompt(
                            HTML("<orange>#init_safe ></orange> Enter Safe address: ")
                        )
                    if rpc_url and safe_address:
                        # Create a Safe instance with the provided RPC URL and address
                        try:
                            # Set Ethereum client URL and Safe address
                            rpc_url = rpc_url
                            ethereum_client = EthereumClient(rpc_url)
                            safe_address = ChecksumAddress(safe_address)

                            safe_instance = Safe(
                                address=safe_address, ethereum_client=ethereum_client
                            )
                            # If the Safe instance is initialized successfully, break the loop
                            if safe_instance:
                                print_formatted_text(
                                    HTML(
                                        "\n<b><green>Safe instance initialized successfully!</green></b>\n"
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
                "\n<b><magenta>Starting interactive transaction builder session...</magenta></b>\n"
            )
        )
        while True:
            try:
                # Prompt for SafeTx parameters
                if not safe_nonce:
                    safe_nonce = prompt_session.prompt(
                        HTML(
                            "<orange>#tx_builder ></orange> Enter Safe nonce (or press Enter to set it automatically): "
                        )
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
                        )
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
                            "<orange>#tx_builder ></orange> Enter number of internal transactions (or press Enter to set to 1): "
                        )
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
                                "<orange>#tx_builder:internal_txs ></orange> Type of transaction (0 for call_contract [default], 1 for erc20_transfer, 2 for raw): "
                            )
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
                                    "<orange>#tx_builder:internal_txs ></orange> Contract address (or press Enter to use ZERO_ADDRESS): "
                                )
                            )
                            if tx_to:
                                tx_to = ChecksumAddress(tx_to)
                            else:
                                tx_to = to_checksum_address(ZERO_ADDRESS)

                            # Prompt for value
                            tx_value = prompt_session.prompt(
                                HTML(
                                    "<orange>#tx_builder:internal_txs ></orange> Value in wei (or press Enter to use 0): "
                                )
                            )
                            if tx_value:
                                tx_value = int(tx_value)
                            else:
                                tx_value = 0

                            # Prompt for operation type
                            tx_operation = prompt_session.prompt(
                                HTML(
                                    "<orange>#tx_builder:internal_txs ></orange> Operation type (0 for call [default], 1 for delegate call): "
                                )
                            )
                            if tx_operation:
                                tx_operation = int(tx_operation)
                            else:
                                tx_operation = 0

                            # Prompt for function signature
                            function_signature: str = prompt_session.prompt(
                                HTML(
                                    "<orange>#tx_builder:internal_txs ></orange> Function signature (e.g. transfer(address,uint256) [default]): "
                                ),
                                default="transfer(address,uint256)",
                            )
                            func_name, params = function_signature.strip().split("(")
                            param_types = (
                                params.rstrip(")").split(",")
                                if params.rstrip(")")
                                else []
                            )
                            param_values = []
                            for i, typ in enumerate(param_types):
                                val: str = prompt_session.prompt(
                                    HTML(
                                        f"<yellow>#tx_builder:internal_txs ></yellow> Parameter #{i + 1} ({typ}): "
                                    )
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
                            from eth_utils import to_bytes

                            tx_data_hex = prompt_session.prompt(
                                HTML(
                                    "<orange>#tx_builder:internal_txs ></orange> Raw data (hex): "
                                )
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
                        multi_send = MultiSend(ethereum_client=ethereum_client)
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
                        "\n\t<b><green>MultiSend transaction created successfully!</green></b>\n"
                    )
                )

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

    # Unknown command handling
    else:
        logger.warning(f"Unknown msig command: {args.msig_command}")
    return 0
