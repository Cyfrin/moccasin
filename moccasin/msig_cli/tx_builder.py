from typing import Optional

from eth_typing import ChecksumAddress

from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.shortcuts import clear as prompt_clear

from safe_eth.safe import Safe, SafeTx
from safe_eth.safe.multi_send import MultiSend, MultiSendOperation
from safe_eth.util.util import to_0x_hex_str

from moccasin.logging import logger
from moccasin.msig_cli.prompts import (
    prompt_safe_nonce,
    prompt_gas_token,
    prompt_internal_txs,
    prompt_single_internal_tx,
    prompt_save_eip712_json,
)
from moccasin.msig_cli.utils import GoBackToPrompt
from moccasin.msig_cli.utils import pretty_print_safe_tx


def handle_multisend_batch(prompt_session, safe_instance, data, to) -> ChecksumAddress:
    """Handle the MultiSend batch decoding and confirmation using prompt helpers."""
    try:
        decoded_batch = MultiSend.from_transaction_data(data)
    except Exception as e:
        decoded_batch = []
        logger.warning(f"Could not decode data as MultiSend batch: {e}")
    if decoded_batch:
        has_delegate = any(
            tx.operation == MultiSendOperation.DELEGATE_CALL for tx in decoded_batch
        )
        multi_send = MultiSend(
            ethereum_client=safe_instance.ethereum_client, call_only=not has_delegate
        )
        multi_send_address = multi_send.address
        from moccasin.msig_cli.prompts import prompt_multisend_batch_confirmation

        if not prompt_multisend_batch_confirmation(
            prompt_session, decoded_batch, multi_send_address, to
        ):
            from moccasin.msig_cli.utils import GoBackToPrompt

            print_formatted_text(
                HTML(
                    "<b><red>Aborting due to user rejection of decoded batch.</red></b>"
                )
            )
            raise GoBackToPrompt
        to = multi_send_address
    elif not to:
        from moccasin.msig_cli.prompts import prompt_target_contract_address

        to = prompt_target_contract_address(prompt_session)
        to = ChecksumAddress(to)
    return to


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
    safe_nonce = prompt_safe_nonce(prompt_session, safe_instance, safe_nonce)
    gas_token = prompt_gas_token(prompt_session, gas_token)
    if not data:
        internal_txs = prompt_internal_txs(prompt_session, prompt_single_internal_tx)
        if len(internal_txs) > 1:
            multi_send = MultiSend(ethereum_client=safe_instance.ethereum_client)
            data = multi_send.build_tx_data(internal_txs)
            to = multi_send.address
            value = 0
            operation = 0
        elif len(internal_txs) == 1:
            tx = internal_txs[0]
            to = tx.to
            value = tx.value
            data = tx.data
            operation = tx.operation.value
    print_formatted_text(
        HTML("\n<b><green>MultiSend transaction created successfully!</green></b>\n")
    )
    if data:
        to = handle_multisend_batch(prompt_session, safe_instance, data, to)
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
