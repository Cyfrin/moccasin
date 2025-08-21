from typing import List, Optional

from eth.constants import ZERO_ADDRESS
from eth_abi.abi import encode as abi_encode
from eth_typing import ChecksumAddress
from eth_utils import function_signature_to_4byte_selector, to_checksum_address
from prompt_toolkit import HTML, print_formatted_text
from safe_eth.safe.multi_send import MultiSendOperation, MultiSendTx

from moccasin.msig_cli.constants import DEFAULT_MULTISEND_SAFE_TX_GAS, LEFT_PROMPT_SIGN
from moccasin.msig_cli.utils.helpers import (
    parse_eth_type_value,
    pretty_print_decoded_multisend,
)
from moccasin.msig_cli.validators import (
    param_type_validators,
    validator_address,
    validator_function_signature,
    validator_not_empty,
    validator_not_zero_number,
    validator_number,
    validator_operation,
    validator_transaction_type,
)


def prompt_safe_nonce(prompt_session) -> int:
    safe_nonce = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Safe nonce? </b>"),
        validator=validator_number,
        placeholder=HTML("<grey>[default: 0]</grey>"),
    )
    if safe_nonce:
        safe_nonce = int(safe_nonce)
    else:
        safe_nonce = 0

    return safe_nonce


def prompt_confirm_safe_nonce(prompt_session, retrieved_safe_nonce: int) -> str:
    return prompt_session.prompt(
        HTML(
            f"{LEFT_PROMPT_SIGN}<b>Change nonce to retrieved Safe nonce ({retrieved_safe_nonce})? </b>"
        ),
        placeholder=HTML("<grey>yes/no</grey>"),
        validator=validator_not_empty,
    )


def prompt_gas_token(prompt_session):
    gas_token = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Gas token address? </b>"),
        validator=validator_address,
        placeholder=HTML("<grey>[default: 0x...]</grey>"),
    )
    if not gas_token:
        gas_token = ZERO_ADDRESS
    return to_checksum_address(gas_token)


def prompt_internal_txs(prompt_session, single_internal_tx_func) -> List[MultiSendTx]:
    internal_txs = []
    nb_internal_txs = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Number of internal txs? </b>"),
        validator=validator_not_zero_number,
        placeholder=HTML("<grey>[default: 1]</grey>"),
    )
    if nb_internal_txs:
        nb_internal_txs = int(nb_internal_txs)
    else:
        nb_internal_txs = 1
    for idx in range(nb_internal_txs):
        internal_txs.append(
            single_internal_tx_func(prompt_session, idx, nb_internal_txs)
        )
    return internal_txs


def prompt_single_internal_tx(
    prompt_session, idx, nb_internal_txs
) -> Optional[MultiSendTx]:
    print_formatted_text(
        HTML(
            f"\n<b><orange>--- Internal Tx {str(idx + 1).zfill(2)}/{str(nb_internal_txs).zfill(2)} ---</orange></b>\n"
        )
    )
    tx_type = prompt_session.prompt(
        HTML(
            f"{LEFT_PROMPT_SIGN}<b>Internal tx type? </b>0: Call, 1: ERC20, 2: Calldata "
        ),
        validator=validator_transaction_type,
        placeholder=HTML("<grey>[default: 0]</grey>"),
    )
    tx_type = int(tx_type) if tx_type else 0
    tx_to = to_checksum_address(ZERO_ADDRESS)
    tx_value = 0
    tx_data = b""
    tx_operation = 0
    if tx_type == 0:
        tx_to, tx_value, tx_operation, tx_data = _handle_internal_tx_call_type(
            prompt_session, tx_to, tx_value, tx_operation
        )
    else:
        print_formatted_text(
            HTML(f"\n<b><red>WIP: Unsupported internal tx type: {tx_type}.</red></b>\n")
        )
        return None
    return MultiSendTx(
        operation=MultiSendOperation.CALL
        if tx_operation == 0
        else MultiSendOperation.DELEGATE_CALL,
        to=tx_to,
        value=int(tx_value),
        data=tx_data,
    )
    # @TODO: Handle other internal tx types (RAW calldata)


def _handle_internal_tx_call_type(prompt_session, tx_to, tx_value, tx_operation):
    tx_to = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Contract address? </b>"),
        validator=validator_address,
        placeholder=HTML("<grey>[default: 0x...]</grey>"),
    )
    tx_to = ChecksumAddress(tx_to) if tx_to else to_checksum_address(ZERO_ADDRESS)
    tx_value = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Value (wei)? </b>"),
        validator=validator_number,
        placeholder=HTML("<grey>[default: 0]</grey>"),
    )
    tx_value = int(tx_value) if tx_value else 0
    tx_operation = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Operation type? </b>"),
        validator=validator_operation,
        placeholder=HTML("<grey>[default: 0]</grey>"),
    )
    tx_operation = int(tx_operation) if tx_operation else 0
    function_signature: str = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Function signature? </b>"),
        validator=validator_function_signature,
        placeholder=HTML("<grey>e.g. transfer(address,uint256) or blank</grey>"),
    )
    tx_data = b""
    if function_signature:
        func_name, params = function_signature.strip().split("(")
        param_types = params.rstrip(")").split(",") if params.rstrip(")") else []
        param_values = []
        for i, typ in enumerate(param_types):
            validator = param_type_validators.get(typ, validator_not_empty)
            val: str = prompt_session.prompt(
                HTML(f"{LEFT_PROMPT_SIGN}<b>Param #{i + 1} ({typ})? </b>"),
                validator=validator,
                placeholder="",
            )
            param_values.append(val)
        parsed_param_values = [
            parse_eth_type_value(v, t) for v, t in zip(param_values, param_types)
        ]
        selector = function_signature_to_4byte_selector(
            f"{func_name}({','.join(param_types)})"
        )
        encoded_args = abi_encode(param_types, parsed_param_values)
        tx_data = selector + encoded_args

    return tx_to, tx_value, tx_operation, tx_data


def prompt_multisend_batch_confirmation(
    prompt_session, decoded_batch, multi_send_address, to
):
    if to and to != multi_send_address:
        print_formatted_text(
            HTML(
                f"{LEFT_PROMPT_SIGN}<yellow>Target address will be overridden with MultiSend: {multi_send_address}</yellow>"
            )
        )
    print_formatted_text(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Decoded MultiSend batch. Correct? </b>")
    )
    pretty_print_decoded_multisend(decoded_batch)
    confirm = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Proceed with batch? </b>"),
        placeholder=HTML("<grey>y/n</grey>"),
        validator=validator_not_empty,
    )
    return confirm.strip().lower() in ("y", "yes")


def prompt_target_contract_address(prompt_session):
    return to_checksum_address(
        prompt_session.prompt(
            HTML(f"{LEFT_PROMPT_SIGN}<b>Target contract address? </b>"),
            placeholder=HTML("<grey>e.g. 0x...</grey>"),
            validator=validator_address,
        )
    )


def prompt_operation_type(prompt_session):
    operation = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Operation type? </b>"),
        validator=validator_operation,
        placeholder=HTML("<grey>[default: 0]</grey>"),
    )
    return int(operation) if operation else int(MultiSendOperation.CALL.value)


def prompt_refund_receiver(prompt_session):
    address = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Refund receiver address? </b>"),
        validator=validator_address,
        placeholder=HTML("<grey>[default: 0x...]</grey>"),
    )

    if address is None or address == "":
        address = ZERO_ADDRESS
    return to_checksum_address(address)


def prompt_safe_tx_gas(prompt_session):
    safe_tx_gas = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>SafeTx gas? </b>"),
        validator=validator_number,
        placeholder=HTML(f"<grey>[default: {DEFAULT_MULTISEND_SAFE_TX_GAS}]</grey>"),
    )
    return int(safe_tx_gas) if safe_tx_gas else DEFAULT_MULTISEND_SAFE_TX_GAS
