from argparse import Namespace
from pathlib import Path
from typing import Optional

from eth_typing import ChecksumAddress
from prompt_toolkit import HTML, PromptSession, print_formatted_text
from safe_eth.safe import Safe, SafeTx
from safe_eth.safe.exceptions import CannotEstimateGas
from safe_eth.safe.multi_send import MultiSend, MultiSendOperation

from moccasin.logging import logger
from moccasin.msig_cli.tx.build_prompts import (
    prompt_base_gas,
    prompt_confirm_safe_nonce,
    prompt_gas_token,
    prompt_internal_txs,
    prompt_multisend_batch_confirmation,
    prompt_refund_receiver,
    prompt_safe_nonce,
    prompt_safe_tx_gas,
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
)

# --- Constants ---
CALL_TX_OPERATION = 0


def _decode_and_confirm_multisend_batch(
    prompt_session, safe_instance, data, to
) -> Optional[ChecksumAddress]:
    """Decode and confirm MultiSend batch. If not a batch, return (None, None).

    :param prompt_session: Prompt session for user input.
    :param safe_instance: Safe instance to decode the MultiSend batch.
    :param data: Data to decode as MultiSend batch.
    :param to: Address to send the MultiSend batch to.
    :return: A tuple containing the address to send the MultiSend batch to
    """
    try:
        decoded_batch = MultiSend.from_transaction_data(data)
    except Exception as e:
        logger.warning(f"Could not decode data as MultiSend batch: {e}")
        return None

    if not decoded_batch:
        return None

    has_delegate = any(
        tx.operation == MultiSendOperation.DELEGATE_CALL for tx in decoded_batch
    )

    # Initialize MultiSend with the address if provided, otherwise use default
    # @NOTE always default to call only operation to avoid issues with delegate calls
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

    return multi_send_address


def _setup_gas_values_to_safe_tx(
    prompt_session: PromptSession,
    safe_instance: Safe,
    to: ChecksumAddress,
    value: int,
    data: bytes,
    gas_token: ChecksumAddress,
) -> tuple[int, int, int]:
    """Setup gas values for the SafeTx.

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
    estimated_base_gas = None

    try:
        estimated_safe_tx_gas = safe_instance.estimate_tx_gas(
            to, value, data, CALL_TX_OPERATION
        )

        print_formatted_text(
            HTML(
                f"<b><green>Estimated gas for SafeTx: </green></b>{estimated_safe_tx_gas}"
            )
        )

        # Get the base gas for the Safe trnsaction
        estimated_base_gas = safe_instance.estimate_tx_base_gas(
            to, value, data, CALL_TX_OPERATION, gas_token, estimated_safe_tx_gas
        )
        print_formatted_text(
            HTML(
                f"<b><green>Estimated base gas for SafeTx: </green></b>{estimated_base_gas}"
            )
        )
    # Catch specific exceptions for gas estimation
    except CannotEstimateGas:
        print_formatted_text(
            HTML(
                "<b><yellow>Warning: Cannot estimate gas for this batch. Please enter a values manually.</yellow></b>"
            )
        )
        # Prompt for manual input or set a default value
        estimated_safe_tx_gas = prompt_safe_tx_gas(prompt_session)
        estimated_base_gas = prompt_base_gas(prompt_session)
    # Catch any other exceptions and raise a more descriptive error
    except Exception as e:
        raise Exception(f"Error setting up and estimating gas for SafeTx: {e}") from e

    # Compare the SafeTx gas price with the Safe's gas price
    estimated_gas_price = safe_instance.w3.eth.gas_price  # see: safe_tx execute method

    return estimated_safe_tx_gas, estimated_base_gas, estimated_gas_price


# --- Main entrypoint ---
def run(
    prompt_session: PromptSession,
    safe_instance: Safe,
    to: Optional[ChecksumAddress] = None,
    value: Optional[int] = None,
    safe_nonce: Optional[int] = None,
    data: Optional[bytes] = None,
    gas_token: Optional[ChecksumAddress] = None,
    refund_receiver: Optional[ChecksumAddress] = None,
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

    # If no Safe nonce provided, prompt for it
    if safe_nonce is None:
        safe_nonce = prompt_safe_nonce(prompt_session)

    # Check if Safe nonce is provided or aligned with the current Safe nonce
    retrieved_safe_nonce = safe_instance.retrieve_nonce()
    if safe_nonce != retrieved_safe_nonce:
        print_formatted_text(
            HTML(
                f"<b><red>Warning: Safe nonce not provided or does not match the estimated Safe nonce ({retrieved_safe_nonce}).</red></b>"
            )
        )
        confirm = prompt_confirm_safe_nonce(prompt_session, retrieved_safe_nonce)
        if confirm.lower() in ("yes", "y"):
            safe_nonce = retrieved_safe_nonce
            print_formatted_text(
                HTML(f"<b><green>Using retrieved Safe nonce: </green></b>{safe_nonce}")
            )
        else:
            print_formatted_text(
                HTML(
                    f"<b><red>Continuing with provided Safe nonce: </red></b>{safe_nonce}"
                )
            )

    # If no gas token provided, prompt for it
    if gas_token is None:
        gas_token = prompt_gas_token(prompt_session)

    # Check for refund receiver
    if refund_receiver is None:
        refund_receiver = prompt_refund_receiver(prompt_session)

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
            print_formatted_text(
                HTML(
                    "\n<b><green>Single internal transaction created successfully!</green></b>\n"
                )
            )

    # If data is provided, try to decode/confirm MultiSend batch
    # @NOTE: maybe use this to display the decoded batch in other commands
    if data is not None:
        to_decoded = _decode_and_confirm_multisend_batch(
            prompt_session, safe_instance, data, to
        )
        if to_decoded is not None:
            to = to_decoded

    # If still missing, prompt for target contract address and/or operation
    if to is None:
        to = prompt_target_contract_address(prompt_session)

    # If value is still None at this point, default to 0
    if value is None:
        value = 0

    # Setup gas values for the SafeTx
    safe_tx_gas, base_gas, gas_price = _setup_gas_values_to_safe_tx(
        prompt_session, safe_instance, to, value, data, gas_token
    )

    try:
        safe_tx = safe_instance.build_multisig_tx(
            to=to,
            value=value,
            operation=CALL_TX_OPERATION,  # Default to CALL operation
            safe_nonce=safe_nonce,
            data=data,
            gas_token=gas_token,
            refund_receiver=refund_receiver,
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
    Optional[bytes],
    Optional[ChecksumAddress],
    Optional[ChecksumAddress],
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
    value = getattr(args, "value", "0")
    safe_nonce = getattr(args, "safe_nonce", None)
    data = getattr(args, "data", None)
    gas_token = getattr(args, "gas_token", None)
    refund_receiver = getattr(args, "refund_receiver", None)
    output_json = getattr(args, "output_json", None)

    if safe_address is not None:
        safe_address = validate_address(safe_address)
    if to is not None:
        to = validate_address(to)
    if value is not None:
        value = validate_number(value)
    if safe_nonce is not None:
        safe_nonce = validate_number(safe_nonce)
    if data is not None:
        data = validate_data(data)
    if gas_token is not None:
        gas_token = validate_address(gas_token)
    if refund_receiver is not None:
        refund_receiver = validate_address(refund_receiver)
    if output_json is not None:
        output_json = validate_json_file(output_json)

    return (
        safe_address,
        to,
        value,
        safe_nonce,
        data,
        gas_token,
        refund_receiver,
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
