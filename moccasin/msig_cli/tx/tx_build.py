from argparse import Namespace
from typing import Optional

from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address
from hexbytes import HexBytes
from prompt_toolkit import HTML, PromptSession, print_formatted_text
from safe_eth.safe import Safe, SafeTx
from safe_eth.safe.multi_send import MultiSend, MultiSendOperation

from moccasin.logging import logger
from moccasin.msig_cli.common_prompts import prompt_save_safe_tx_json
from moccasin.msig_cli.tx.build_prompts import (
    prompt_gas_token,
    prompt_internal_txs,
    prompt_multisend_batch_confirmation,
    prompt_operation_type,
    prompt_safe_nonce,
    prompt_single_internal_tx,
    prompt_target_contract_address,
)
from moccasin.msig_cli.utils.helpers import (
    get_custom_eip712_structured_data,
    get_multisend_address_from_env,
    pretty_print_safe_tx,
    save_safe_tx_json,
)
from moccasin.msig_cli.validators import (
    validate_address,
    validate_data,
    validate_json_file,
    validate_number,
    validate_operation,
)


def _decode_and_confirm_multisend_batch(
    prompt_session, safe_instance, data, to, operation
) -> tuple[Optional[ChecksumAddress], Optional[int]]:
    """Decode and confirm MultiSend batch. If not a batch, return (None, None)."""
    try:
        decoded_batch = MultiSend.from_transaction_data(data)
    except Exception as e:
        logger.warning(f"Could not decode data as MultiSend batch: {e}")
        return None, None

    if not decoded_batch:
        return None, None

    has_delegate = any(
        tx.operation == MultiSendOperation.DELEGATE_CALL for tx in decoded_batch
    )

    # Initialize MultiSend with the address if provided, otherwise use default
    multi_send = MultiSend(
        ethereum_client=safe_instance.ethereum_client,
        address=get_multisend_address_from_env(),
        call_only=not has_delegate,
    )
    multi_send_address = multi_send.address

    if not prompt_multisend_batch_confirmation(
        prompt_session, decoded_batch, multi_send_address, to
    ):
        print_formatted_text(
            HTML("<b><red>Aborting due to user rejection of decoded batch.</red></b>")
        )
        raise Exception("User rejected MultiSend batch confirmation.")

    to = multi_send_address
    operation = int(
        MultiSendOperation.DELEGATE_CALL.value
        if has_delegate
        else MultiSendOperation.CALL.value
    )
    return to, operation


# --- Main entrypoint ---
def run(
    prompt_session: PromptSession,
    safe_instance: Safe,
    to: Optional[str] = None,
    value: Optional[int] = None,
    operation: Optional[int] = None,
    safe_nonce: Optional[int] = None,
    data: Optional[HexBytes] = None,
    gas_token: Optional[str] = None,
    output_json: Optional[str] = None,
) -> SafeTx:
    """Run the transaction builder with interactive prompts.

    :param prompt_session: Prompt session for user input.
    :param safe_instance: Safe instance to build the transaction for.
    :param to: Address of the contract to call.
    :param value: Value to send with the transaction, in wei.
    :param operation: Operation type (0 for call, 1 for delegate call).
    :param safe_nonce: Nonce of the Safe contract to use for the transaction.
    :param data: Data to send with the transaction, in hex format.
    :param gas_token: Token to use for gas, defaults to the native token of the network.
    :param eip712_json_out: Output file to save the EIP-712 structured data as JSON.

    :return: An instance of SafeTx.
    """
    # Get input values from args
    tx_to = to_checksum_address(to) if to else None
    tx_gas_token = to_checksum_address(gas_token) if gas_token else None
    tx_value = value if value is not None else 0
    tx_operation = operation
    tx_data = data
    tx_safe_nonce = safe_nonce
    tx_output_json = output_json

    # Prompt for nonce and gas token
    if tx_safe_nonce is None:
        tx_safe_nonce = prompt_safe_nonce(prompt_session, safe_instance)
    if not tx_gas_token:
        tx_gas_token = prompt_gas_token(prompt_session)

    # If no data provided, we prompt for internal transactions
    if tx_data is None:
        internal_txs = prompt_internal_txs(prompt_session, prompt_single_internal_tx)
        if len(internal_txs) > 1:
            multi_send = MultiSend(
                ethereum_client=safe_instance.ethereum_client,
                address=get_multisend_address_from_env(),
            )
            tx_data = multi_send.build_tx_data(internal_txs)
            tx_to = multi_send.address
            tx_operation = int(
                MultiSendOperation.CALL.value
                if multi_send.call_only
                else MultiSendOperation.DELEGATE_CALL.value
            )
            print_formatted_text(
                HTML(
                    "\n<b><green>MultiSend transaction created successfully!</green></b>\n"
                )
            )
        else:
            multi_send_one_tx = internal_txs[0]
            tx_to = multi_send_one_tx.to
            tx_value = multi_send_one_tx.value
            tx_data = multi_send_one_tx.data
            tx_operation = multi_send_one_tx.operation.value
            print_formatted_text(
                HTML(
                    "\n<b><green>Single internal transaction created successfully!</green></b>\n"
                )
            )

    # If data is provided, try to decode/confirm MultiSend batch
    if tx_data is not None:
        to_decoded, op_decoded = _decode_and_confirm_multisend_batch(
            prompt_session, safe_instance, tx_data, tx_to, tx_operation
        )
        if to_decoded is not None and op_decoded is not None:
            tx_to, tx_operation = to_decoded, op_decoded

    # If still missing, prompt for target contract address and/or operation
    if not tx_to:
        tx_to = prompt_target_contract_address(prompt_session)
    if tx_operation is None:
        tx_operation = prompt_operation_type(prompt_session)
    try:
        safe_tx = safe_instance.build_multisig_tx(
            to=tx_to,
            value=tx_value,
            operation=tx_operation,
            safe_nonce=tx_safe_nonce,
            data=tx_data,
            gas_token=tx_gas_token,
        )
    except Exception as e:
        raise Exception(f"Error creating SafeTx instance: {e}") from e
    print_formatted_text(
        HTML("\n<b><green>SafeTx instance created successfully!</green></b>\n")
    )
    # Pretty-print the SafeTx fields and get EIP-712 structured data
    pretty_print_safe_tx(safe_tx)
    safe_tx_data = get_custom_eip712_structured_data(safe_tx)

    # Save EIP-712 structured data as JSON
    if tx_output_json is None:
        tx_output_json = prompt_save_safe_tx_json(prompt_session)

    if tx_output_json is not None:
        save_safe_tx_json(tx_output_json, safe_tx_data)
    else:
        print_formatted_text(HTML("<b><yellow>Not saving EIP-712 JSON.</yellow></b>"))

    return safe_tx


# --- Tx build helper functions ---
def preprocess_raw_args(
    args: Namespace,
) -> tuple[
    Optional[ChecksumAddress],
    Optional[int],
    Optional[int],
    Optional[int],
    Optional[HexBytes],
    Optional[ChecksumAddress],
    Optional[str],
]:
    """Preprocess and validate raw arguments for the transaction builder.

    :param to: Address of the contract to call.
    :param value: Value to send with the transaction, in wei.
    :param operation: Operation type (0 for call, 1 for delegate call).
    :param safe_nonce: Nonce of the Safe contract to use for the transaction.
    :param data: Data to send with the transaction, in hex format.
    :param gas_token: Token to use for gas, defaults to the native token of the network.
    :param output_json: Output file to save the EIP-712 structured data as JSON.
    :return: A tuple containing the validated and converted values.
    """
    safe_address = getattr(args, "safe_address", None)
    to = getattr(args, "to", None)
    value = getattr(args, "value", None)
    operation = getattr(args, "operation", None)
    safe_nonce = getattr(args, "safe_nonce", None)
    data = getattr(args, "data", None)
    gas_token = getattr(args, "gas_token", None)
    output_json = getattr(args, "output_json", None)

    if safe_address is not None:
        safe_address = validate_address(safe_address)
    if to is not None:
        to = validate_address(to)
    if value is not None:
        value = validate_number(value)
    if operation is not None:
        operation = validate_operation(operation)
    if safe_nonce is not None:
        safe_nonce = validate_number(safe_nonce)
    if data is not None:
        data = validate_data(data)
    if gas_token is not None:
        gas_token = validate_address(gas_token)
    if output_json is not None:
        output_json = validate_json_file(output_json)

    return safe_address, to, value, operation, safe_nonce, data, gas_token, output_json
