from ast import Mult
from re import M
from typing import Optional

from eth_typing import ChecksumAddress

from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.shortcuts import clear as prompt_clear

from regex import T
from safe_eth.safe import Safe, SafeTx
from safe_eth.safe.multi_send import MultiSend, MultiSendOperation
from safe_eth.util.util import to_0x_hex_str

from moccasin.logging import logger
from moccasin.msig_cli.prompts import (
    prompt_operation_type,
    prompt_safe_nonce,
    prompt_gas_token,
    prompt_internal_txs,
    prompt_single_internal_tx,
    prompt_save_eip712_json,
    prompt_multisend_batch_confirmation,
    prompt_target_contract_address,
)
from moccasin.msig_cli.utils import GoBackToPrompt, pretty_print_safe_tx


def _handle_multisend_batch(
    prompt_session, safe_instance, data, _to, _operation
) -> tuple[ChecksumAddress, int]:
    """Handle the MultiSend batch decoding and confirmation using prompt helpers.

    :param prompt_session: Prompt session for user input.
    :param safe_instance: Safe instance to build the transaction for.
    :param data: Data to decode as MultiSend batch.
    :param to: Target address for the transaction, if not provided will prompt for it.

    :return: Tuple of (to address, operation).
    """
    to: ChecksumAddress = _to
    operation: int = _operation
    # Decode the MultiSend batch from the provided data
    try:
        decoded_batch = MultiSend.from_transaction_data(data)
    except Exception as e:
        decoded_batch = []
        logger.warning(f"Could not decode data as MultiSend batch: {e}")

    # If we have a decoded batch, check if it contains delegate calls
    if decoded_batch:
        has_delegate = any(
            tx.operation == MultiSendOperation.DELEGATE_CALL for tx in decoded_batch
        )

        multi_send = MultiSend(
            ethereum_client=safe_instance.ethereum_client, call_only=not has_delegate
        )
        multi_send_address = multi_send.address

        if not prompt_multisend_batch_confirmation(
            prompt_session, decoded_batch, multi_send_address, to
        ):
            print_formatted_text(
                HTML(
                    "<b><red>Aborting due to user rejection of decoded batch.</red></b>"
                )
            )
            raise GoBackToPrompt

        # Overwrite the to address and operation with the MultiSend address and operation
        to = multi_send_address
        operation = int(
            MultiSendOperation.DELEGATE_CALL.value
            if has_delegate
            else MultiSendOperation.CALL.value
        )

    # If it is not a MultiSend batch, we need to prompt for the target address
    if not to:
        to = prompt_target_contract_address(prompt_session)
        to = ChecksumAddress(to)

    # If no operation provided, we prompt for it
    if operation is None:
        operation = prompt_operation_type(prompt_session)
    return (to, operation)


def save_eip712_json(prompt_session, eip712_struct, eip712_json_out=None):
    """Save the EIP-712 structured data to a JSON file using prompt helper."""
    prompt_save_eip712_json(prompt_session, eip712_struct, eip712_json_out)


# --- Main entrypoint ---
def run(
    prompt_session: PromptSession,
    safe_instance: Safe,
    to: Optional[str] = None,
    value: Optional[int] = None,
    operation: Optional[int] = None,
    safe_nonce: Optional[int] = None,
    data: Optional[bytes] = None,
    gas_token: Optional[str] = None,
    eip712_json_out: Optional[str] = None,
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
    :raises GoBackToPrompt: If we ne to go back to the main CLI prompt.
    """
    safe_nonce = prompt_safe_nonce(
        prompt_session, safe_instance, safe_nonce, cmd="tx_builder"
    )
    gas_token = prompt_gas_token(prompt_session, gas_token, cmd="tx_builder")

    # If no data provided, we prompt for internal transactions
    if not data:
        internal_txs = prompt_internal_txs(
            prompt_session, prompt_single_internal_tx, cmd="tx_builder"
        )
        if len(internal_txs) > 1:
            multi_send = MultiSend(ethereum_client=safe_instance.ethereum_client)
            data = multi_send.build_tx_data(internal_txs)
            to = multi_send.address
            value = 0
            operation = int(
                MultiSendOperation.CALL.value
                if multi_send.is_call_only
                else MultiSendOperation.DELEGATE_CALL.value
            )
            print_formatted_text(
                HTML(
                    "\n<b><green>MultiSend transaction created successfully!</green></b>\n"
                )
            )
        elif len(internal_txs) == 1:
            tx = internal_txs[0]
            to = tx.to
            value = tx.value
            data = tx.data
            operation = tx.operation.value
            print_formatted_text(
                HTML(
                    "\n<b><green>Single internal transaction created successfully!</green></b>\n"
                )
            )

    # If data is provided or we double check the batch confirmation
    if data:
        to, operation = _handle_multisend_batch(
            prompt_session, safe_instance, data, to, operation
        )
    try:
        safe_tx = safe_instance.build_multisig_tx(
            to=to,
            value=value,
            operation=operation,
            safe_nonce=safe_nonce,
            data=data,
            gas_token=gas_token,
        )
    except Exception as e:
        logger.error(f"Failed to create SafeTx instance: {e}")
        raise GoBackToPrompt
    prompt_clear()
    print_formatted_text(
        HTML("\n<b><green>SafeTx instance created successfully!</green></b>\n")
    )
    pretty_print_safe_tx(safe_tx)
    eip712_struct = safe_tx.eip712_structured_data
    eip712_struct["message"]["data"] = to_0x_hex_str(eip712_struct["message"]["data"])
    save_eip712_json(prompt_session, eip712_struct, eip712_json_out)

    return safe_tx
