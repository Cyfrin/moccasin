from typing import List, Optional

from eth.constants import ZERO_ADDRESS
from eth_utils import to_checksum_address
from prompt_toolkit import HTML, print_formatted_text
from safe_eth.safe.multi_send import MultiSendOperation, MultiSendTx

from moccasin.msig_cli.constants import DEFAULT_MULTISEND_SAFE_TX_GAS, LEFT_PROMPT_SIGN
from moccasin.msig_cli.utils.enums import TxBuildDataType
from moccasin.msig_cli.utils.helpers import build_tx_data_from_function_signature
from moccasin.msig_cli.validators import (
    get_param_validator,
    validator_empty_or_address,
    validator_empty_or_function_signature,
    validator_empty_or_not_zero_number,
    validator_empty_or_number,
    validator_empty_or_operation,
    validator_empty_or_tx_build_data_type,
    validator_empty_or_bytes_hex,
)


def prompt_safe_nonce(prompt_session) -> int:
    safe_nonce = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Safe nonce? </b>"),
        validator=validator_empty_or_number,
        placeholder=HTML("<grey>[default: 0]</grey>"),
    )
    if safe_nonce:
        safe_nonce = int(safe_nonce)
    else:
        safe_nonce = 0

    return safe_nonce


def prompt_gas_token(prompt_session):
    gas_token = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Gas token address? </b>"),
        validator=validator_empty_or_address,
        placeholder=HTML("<grey>[default: 0x...]</grey>"),
    )
    if not gas_token:
        gas_token = ZERO_ADDRESS
    return to_checksum_address(gas_token)


def prompt_internal_txs(prompt_session, single_internal_tx_func) -> List[MultiSendTx]:
    internal_txs = []
    nb_internal_txs = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Number of internal txs? </b>"),
        validator=validator_empty_or_not_zero_number,
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
    # Prompt for common transaction fields
    tx_to = prompt_target_address(prompt_session)
    tx_value = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Value (wei)? </b>"),
        validator=validator_empty_or_number,
        placeholder=HTML("<grey>[default: 0]</grey>"),
    )
    tx_value = int(tx_value) if tx_value else 0
    tx_operation = prompt_operation_type(prompt_session)
    tx_operation = int(tx_operation) if tx_operation else 0

    # See how to build call data from function signature or raw data
    # 0: MANUAL, 1: RAW_DATA
    tx_type = prompt_session.prompt(
        HTML(
            f"{LEFT_PROMPT_SIGN}<b>Data building mode? </b>{TxBuildDataType.MANUAL.value} - Manual, {TxBuildDataType.RAW_DATA.value} - Raw data "
        ),
        validator=validator_empty_or_tx_build_data_type,
        placeholder=HTML("<grey>[default: 0]</grey>"),
    )
    tx_type = int(tx_type) if tx_type else 0

    # Handle manual transaction building
    tx_data = None
    if tx_type == 0:
        tx_data = _handle_internal_tx_building_data(prompt_session)
    # Handle raw data transaction building
    elif tx_type == 1:
        tx_data = _handle_internal_tx_raw_data(prompt_session)
    else:
        print_formatted_text(
            HTML(f"\n<b><red>Unsupported internal tx type: {tx_type}.</red></b>\n")
        )
        return None

    # Create and return the MultiSendTx object
    return MultiSendTx(
        operation=MultiSendOperation.CALL
        if tx_operation == 0
        else MultiSendOperation.DELEGATE_CALL,
        to=tx_to,
        value=int(tx_value),
        data=tx_data,
    )


def _handle_internal_tx_building_data(prompt_session) -> bytes:
    """Handle the manual transaction building for call type."""
    function_signature: str = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Function signature? </b>"),
        validator=validator_empty_or_function_signature,
        placeholder=HTML("<grey>e.g. transfer(address,uint256) or blank</grey>"),
    )
    tx_data = b""
    if function_signature:
        func_name, params = function_signature.strip().split("(")
        # Remove spaces around each type inside parentheses
        param_types = (
            [t.strip() for t in params.rstrip(")").split(",")]
            if params.rstrip(")")
            else []
        )
        param_values = []
        for i, typ in enumerate(param_types):
            validator = get_param_validator(typ)
            val: str = prompt_session.prompt(
                HTML(f"{LEFT_PROMPT_SIGN}<b>Param #{i + 1} ({typ})? </b>"),
                validator=validator,
                placeholder="",
            )
            param_values.append(val)
        tx_data = build_tx_data_from_function_signature(
            func_name, param_types, param_values
        )

    return tx_data


def _handle_internal_tx_raw_data(prompt_session) -> bytes:
    """Handle the raw data transaction building for call type."""
    tx_data = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Raw data (hex, bytes)? </b>"),
        validator=validator_empty_or_bytes_hex,
        placeholder=HTML("<grey>[default: 0x...]</grey>"),
    )
    # Convert to bytes if provided
    if tx_data is None:
        tx_data = b""
    else:
        data_str = str(tx_data).strip()
        if data_str.startswith("0x"):
            tx_data = bytes.fromhex(data_str[2:])
        else:
            tx_data = bytes.fromhex(data_str)
    return tx_data


def prompt_target_address(prompt_session):
    return to_checksum_address(
        prompt_session.prompt(
            HTML(f"{LEFT_PROMPT_SIGN}<b>Target address? </b>"),
            placeholder=HTML("<grey>[default: 0x...]</grey>"),
            validator=validator_empty_or_address,
        )
        or to_checksum_address(ZERO_ADDRESS)
    )


def prompt_operation_type(prompt_session):
    operation = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Operation type? </b>"),
        validator=validator_empty_or_operation,
        placeholder=HTML("<grey>[default: 0]</grey>"),
    )
    return int(operation) if operation else int(MultiSendOperation.CALL.value)


def prompt_refund_receiver(prompt_session):
    address = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Refund receiver address? </b>"),
        validator=validator_empty_or_address,
        placeholder=HTML("<grey>[default: 0x...]</grey>"),
    )

    if address is None or address == "":
        address = ZERO_ADDRESS
    return to_checksum_address(address)


def prompt_safe_tx_gas(prompt_session):
    safe_tx_gas = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>SafeTx gas? </b>"),
        validator=validator_empty_or_number,
        placeholder=HTML(f"<grey>[default: {DEFAULT_MULTISEND_SAFE_TX_GAS}]</grey>"),
    )
    return int(safe_tx_gas) if safe_tx_gas else DEFAULT_MULTISEND_SAFE_TX_GAS
