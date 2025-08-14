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
    get_eip712_structured_data,
    get_multisend_address_from_env,
    pretty_print_safe_tx,
)


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
    json_output: Optional[str] = None,
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
    safe_tx_data = get_eip712_structured_data(safe_tx)

    # Save EIP-712 structured data as JSON
    prompt_save_safe_tx_json(prompt_session, safe_tx_data, json_output)

    return safe_tx


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
