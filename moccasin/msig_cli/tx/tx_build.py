from argparse import Namespace
from pathlib import Path
from typing import Optional

from eth.constants import ZERO_ADDRESS
from eth_typing import ChecksumAddress
from prompt_toolkit import HTML, PromptSession, print_formatted_text
from safe_eth.safe import Safe, SafeTx
from safe_eth.safe.multi_send import MultiSend, MultiSendOperation

from moccasin.logging import logger
from moccasin.msig_cli.tx.build_prompts import (
    prompt_confirm_base_gas_limit,
    prompt_confirm_gas_price,
    prompt_confirm_safe_tx_gas_limit,
    prompt_gas_token,
    prompt_internal_txs,
    prompt_multisend_batch_confirmation,
    prompt_operation_type,
    prompt_safe_nonce,
    prompt_single_internal_tx,
    prompt_target_contract_address,
)
from moccasin.msig_cli.utils.helpers import (
    get_multisend_address_from_env,
    pretty_print_safe_tx,
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
    """Decode and confirm MultiSend batch. If not a batch, return (None, None).

    :param prompt_session: Prompt session for user input.
    :param safe_instance: Safe instance to decode the MultiSend batch.
    :param data: Data to decode as MultiSend batch.
    :param to: Address to send the MultiSend batch to.
    :param operation: Operation type (0 for call, 1 for delegate call).
    :return: A tuple containing the address to send the MultiSend batch to and the operation type.
    """
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


def _setup_gas_values_to_safe_tx(
    prompt_session: PromptSession,
    safe_instance: Safe,
    to: ChecksumAddress,
    value: int,
    data: bytes,
    operation: int,
    gas_token: Optional[ChecksumAddress],
    safe_tx_gas: Optional[int],
    base_gas: Optional[int],
    gas_price: Optional[int],
) -> tuple[int, int, int]:
    """Setup gas values for the SafeTx.

    :param prompt_session: Prompt session for user input.
    :param safe_instance: Safe instance to build the transaction for.
    :param to: Address of the contract to call.
    :param value: Value to send with the transaction, in wei.
    :param data: Data to send with the transaction, in hex format.
    :param operation: Operation type (0 for call, 1 for delegate call).
    :param gas_token: Token to use for gas, defaults to the native token of the network.
    :param safe_tx_gas: Safe transaction gas limit.
    :param base_gas: Base gas for the Safe transaction.
    :param gas_price: Gas price for the Safe transaction.
    :return: A tuple containing the updated safe_tx_gas, base_gas, and gas_price.
    """
    # Estimate the gas for the SafeTx
    estimated_safe_tx_gas = None
    try:
        estimated_safe_tx_gas = safe_instance.estimate_tx_gas(
            to, value, data, operation
        )
    except Exception as e:
        raise Exception(f"Error estimating gas for SafeTx: {e}") from e

    print_formatted_text(
        HTML(f"<b><green>Estimated gas for SafeTx: </green></b>{estimated_safe_tx_gas}")
    )

    # Compare the gas estimate with the SafeTx gas limit
    if safe_tx_gas < estimated_safe_tx_gas:
        print_formatted_text(
            HTML(
                f"<b><red>Warning: SafeTx gas limit ({safe_tx_gas}) is less than the estimated gas ({estimated_safe_tx_gas}).</red></b>"
            )
        )
        # Ask user if they want to change the gas limit or continue with the current gas limit
        confirm = prompt_confirm_safe_tx_gas_limit(
            prompt_session, estimated_safe_tx_gas
        )
        if confirm.lower() in ("yes", "y"):
            safe_tx_gas = estimated_safe_tx_gas
            print_formatted_text(
                HTML(
                    f"<b><green>SafeTx gas limit updated to: </green></b>{safe_tx_gas}"
                )
            )
        else:
            print_formatted_text(
                HTML(
                    f"<b><yellow>Continuing with current SafeTx gas limit: </yellow></b>{safe_tx_gas}"
                )
            )

    # Get the base gas for the Safe trnsaction
    estimated_base_gas = None
    try:
        estimated_base_gas = safe_instance.estimate_tx_base_gas(
            to, value, data, operation, gas_token, safe_tx_gas
        )
    except Exception as e:
        raise Exception(f"Error estimating base gas for SafeTx: {e}") from e
    print_formatted_text(
        HTML(
            f"<b><green>Estimated base gas for SafeTx: </green></b>{estimated_base_gas}"
        )
    )

    # Compare the base gas with the SafeTx base gas
    if base_gas < estimated_base_gas:
        print_formatted_text(
            HTML(
                f"<b><red>Warning: SafeTx base gas ({base_gas}) is less than the estimated base gas ({estimated_base_gas}).</red></b>"
            )
        )
        # Ask user if they want to change the base gas or continue with the current base gas
        confirm = prompt_confirm_base_gas_limit(prompt_session, estimated_base_gas)
        if confirm.lower() in ("yes", "y"):
            base_gas = estimated_base_gas
            print_formatted_text(
                HTML(f"<b><green>SafeTx base gas updated to: </green></b>{base_gas}")
            )
        else:
            print_formatted_text(
                HTML(
                    f"<b><yellow>Continuing with current SafeTx base gas: </yellow></b>{base_gas}"
                )
            )

    # Compare the SafeTx gas price with the Safe's gas price
    estimated_gas_price = safe_instance.w3.eth.gas_price  # see: safe_tx execute method
    if gas_price <= estimated_gas_price:
        print_formatted_text(
            HTML(
                f"<b><red>Warning: SafeTx gas price ({gas_price}) is less than to the Safe's gas price ({estimated_gas_price}).</red></b>"
            )
        )

        # Ask user if they want to change the gas price or do nothing
        confirm = prompt_confirm_gas_price(prompt_session, estimated_gas_price)
        if confirm.lower() in ("yes", "y"):
            gas_price = estimated_gas_price
            print_formatted_text(
                HTML(f"<b><green>SafeTx gas price updated to: </green></b>{gas_price}")
            )
        else:
            print_formatted_text(
                HTML(
                    f"<b><yellow>Continuing with current SafeTx gas price: </yellow></b>{gas_price}"
                )
            )

    return safe_tx_gas, base_gas, gas_price


# --- Main entrypoint ---
def run(
    prompt_session: PromptSession,
    safe_instance: Safe,
    to: Optional[ChecksumAddress] = None,
    value: Optional[int] = None,
    operation: Optional[int] = None,
    safe_nonce: Optional[int] = None,
    data: Optional[bytes] = None,
    gas_token: Optional[ChecksumAddress] = None,
    safe_tx_gas: Optional[int] = None,
    base_gas: Optional[int] = None,
    gas_price: Optional[int] = None,
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

    # Check if safe contract balance is not zero
    if safe_instance.ethereum_client.get_balance(safe_instance.address) <= 0:
        # @FIXME erc20 balance check
        # gas_token is not None
        # and gas_token != ZERO_ADDRESS
        # and safe_instance.ethereum_client.erc20.get_balance(
        #     safe_instance.address, gas_token
        # )
        # <= 0
        raise ValueError(
            "Safe contract does not have any funds. Please fund the Safe contract to run gas simulation"
        )

    # Prompt for nonce and gas token
    if safe_nonce is None:
        safe_nonce = prompt_safe_nonce(prompt_session, safe_instance)
    if not gas_token:
        gas_token = prompt_gas_token(prompt_session)

    # If no data provided, we prompt for internal transactions
    if data is None:
        internal_txs = prompt_internal_txs(prompt_session, prompt_single_internal_tx)
        if len(internal_txs) > 1:
            multi_send = MultiSend(
                ethereum_client=safe_instance.ethereum_client,
                address=get_multisend_address_from_env(),
            )
            data = multi_send.build_tx_data(internal_txs)
            to = multi_send.address
            operation = int(
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
            to = multi_send_one_tx.to
            value = multi_send_one_tx.value
            data = multi_send_one_tx.data
            operation = multi_send_one_tx.operation.value
            print_formatted_text(
                HTML(
                    "\n<b><green>Single internal transaction created successfully!</green></b>\n"
                )
            )

    # If data is provided, try to decode/confirm MultiSend batch
    if data is not None:
        to_decoded, op_decoded = _decode_and_confirm_multisend_batch(
            prompt_session, safe_instance, data, to, operation
        )
        if to_decoded is not None and op_decoded is not None:
            to, operation = to_decoded, op_decoded

    # If still missing, prompt for target contract address and/or operation
    if not to:
        to = prompt_target_contract_address(prompt_session)
    if operation is None:
        operation = prompt_operation_type(prompt_session)

    # Setup gas values for the SafeTx
    safe_tx_gas, base_gas, gas_price = _setup_gas_values_to_safe_tx(
        prompt_session,
        safe_instance,
        to,
        value,
        data,
        operation,
        gas_token,
        safe_tx_gas,
        base_gas,
        gas_price,
    )

    try:
        safe_tx = safe_instance.build_multisig_tx(
            to=to,
            value=value,
            operation=operation,
            safe_nonce=safe_nonce,
            data=data,
            gas_token=gas_token,
            safe_tx_gas=safe_tx_gas,
            base_gas=base_gas,
            gas_price=gas_price,
        )
    except Exception as e:
        raise Exception(f"Error creating SafeTx instance: {e}") from e
    print_formatted_text(
        HTML("\n<b><green>SafeTx instance created successfully!</green></b>\n")
    )
    # Pretty-print the SafeTx fields and get EIP-712 structured data
    pretty_print_safe_tx(safe_tx)

    return safe_tx


# --- Tx build helper functions ---
def preprocess_raw_args(
    args: Namespace | None,
) -> tuple[
    Optional[ChecksumAddress],
    Optional[ChecksumAddress],
    Optional[int],
    Optional[int],
    Optional[int],
    Optional[bytes],
    Optional[ChecksumAddress],
    Optional[int],
    Optional[int],
    Optional[int],
    Optional[Path],
]:
    """Preprocess and validate raw arguments for the transaction builder.

    :param args: Namespace containing raw arguments.
    :return: A tuple containing the validated and converted values.
    """
    if args is None:
        return None, None, None, None, None, None, None, None

    safe_address = getattr(args, "safe_address", None)
    to = getattr(args, "to", None)
    value = getattr(args, "value", 0)
    operation = getattr(args, "operation", None)
    safe_nonce = getattr(args, "safe_nonce", None)
    data = getattr(args, "data", None)
    gas_token = getattr(args, "gas_token", None)
    safe_tx_gas = getattr(args, "safe_tx_gas", 0)
    base_gas = getattr(args, "base_gas", 0)
    gas_price = getattr(args, "gas_price", 0)
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
    if safe_tx_gas is not None:
        safe_tx_gas = validate_number(safe_tx_gas)
    if base_gas is not None:
        base_gas = validate_number(base_gas)
    if gas_price is not None:
        gas_price = validate_number(gas_price)
    if output_json is not None:
        output_json = validate_json_file(output_json)

    return (
        safe_address,
        to,
        value,
        operation,
        safe_nonce,
        data,
        gas_token,
        safe_tx_gas,
        base_gas,
        gas_price,
        output_json,
    )


"""
XXX Exception: Failed to broadcast SafeTx with provided parameters: 
Error broadcasting SafeTx with account 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266: 
('execution reverted: GS026', '0x08c379a000000000000000000000000000000000000000000000000000
0000000000002000000000000000000000000000000000000000000000000000000000000000054
753303236000000000000000000000000000000000000000000000000000000')



The error execution reverted: GS026 means "Invalid owner provided" in Gnosis Safe contracts.

Why is this happening?
The Safe contract checks that all signatures are from valid owners.
If any signature is from an address not in the Safe's owner list, the transaction is rejected with GS026.
What to check:
Safe Owners List

Query the Safe contract for its owners:
Make sure the signers in your SafeTx:
are all present in the Safe's owner list.
Threshold

If your Safe's threshold is 2, you need 2 valid owner signatures.
No Extra Signatures

Do not include signatures from non-owners.
Address Format

Make sure addresses are checksummed and match exactly.
"""
