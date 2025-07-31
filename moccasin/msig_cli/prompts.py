"""
Prompt helper functions for msig_cli, decoupled from msig_cli state.
"""

from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address
from eth.constants import ZERO_ADDRESS
from prompt_toolkit import HTML
from moccasin.msig_cli.validators import (
    validator_address,
    validator_number,
    validator_not_zero_number,
    validator_operation,
    validator_data,
    validator_transaction_type,
    validator_function_signature,
    validator_not_empty,
    param_type_validators,
)


def prompt_safe_nonce(prompt_session, safe_instance, safe_nonce):
    if not safe_nonce:
        safe_nonce = prompt_session.prompt(
            HTML("<orange>#tx_builder ></orange> Enter Safe nonce: "),
            validator=validator_number,
            placeholder=HTML("<grey>[default: auto retrieval]</grey>"),
        )
        if safe_nonce:
            safe_nonce = int(safe_nonce)
        else:
            safe_nonce = safe_instance.retrieve_nonce()
    return safe_nonce


def prompt_gas_token(prompt_session, gas_token):
    if not gas_token:
        gas_token = prompt_session.prompt(
            HTML(
                "<orange>#tx_builder ></orange> Enter gas token address (or press Enter to use ZERO_ADDRESS): "
            ),
            validator=validator_address,
            placeholder=HTML("<grey>[default: 0x...]</grey>"),
        )
        if gas_token:
            gas_token = ChecksumAddress(gas_token)
        else:
            gas_token = to_checksum_address(ZERO_ADDRESS)
    return gas_token


def prompt_internal_txs(prompt_session, single_internal_tx_func):
    internal_txs = []
    nb_internal_txs = prompt_session.prompt(
        HTML("<orange>#tx_builder ></orange> Enter number of internal transactions: "),
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


def prompt_single_internal_tx(prompt_session, idx, nb_internal_txs):
    from prompt_toolkit import HTML, print_formatted_text
    from eth_typing import ChecksumAddress
    from eth.constants import ZERO_ADDRESS
    from eth_utils import to_bytes
    from safe_eth.safe.multi_send import MultiSendTx, MultiSendOperation

    print_formatted_text(
        HTML(
            f"\n\t<b><magenta>--- Transaction {str(idx + 1).zfill(2)}/{str(nb_internal_txs).zfill(2)} ---</magenta></b>\n"
        )
    )
    tx_type = prompt_session.prompt(
        HTML(
            "<orange>#tx_builder:internal_txs ></orange> Type of transaction (0 for call_contract, 1 for erc20_transfer, 2 for raw): "
        ),
        validator=validator_transaction_type,
        placeholder=HTML("<grey>[default: 0 for call_contract]</grey>"),
    )
    tx_type = int(tx_type) if tx_type else 0
    tx_to = ChecksumAddress(ZERO_ADDRESS)
    tx_value = 0
    tx_data = b""
    tx_operation = 0
    if tx_type == 0:
        tx_to = prompt_session.prompt(
            HTML("<orange>#tx_builder:internal_txs ></orange> Contract address: "),
            validator=validator_address,
            placeholder=HTML("<grey>[default: 0x...]</grey>"),
        )
        tx_to = ChecksumAddress(tx_to) if tx_to else to_checksum_address(ZERO_ADDRESS)
        tx_value = prompt_session.prompt(
            HTML("<orange>#tx_builder:internal_txs ></orange> Value in wei: "),
            validator=validator_number,
            placeholder=HTML("<grey>[default: 0]</grey>"),
        )
        tx_value = int(tx_value) if tx_value else 0
        tx_operation = prompt_session.prompt(
            HTML(
                "<orange>#tx_builder:internal_txs ></orange> Operation type (0 for call, 1 for delegate call): "
            ),
            validator=validator_operation,
            placeholder=HTML("<grey>[default: 0 for call]</grey>"),
        )
        tx_operation = int(tx_operation) if tx_operation else 0
        function_signature: str = prompt_session.prompt(
            HTML("<orange>#tx_builder:internal_txs ></orange> Function signature: "),
            validator=validator_function_signature,
            placeholder=HTML("<grey>e.g. transfer(address,uint256)</grey>"),
        )
        func_name, params = function_signature.strip().split("(")
        param_types = params.rstrip(")").split(",") if params.rstrip(")") else []
        param_values = []
        for i, typ in enumerate(param_types):
            validator = param_type_validators.get(typ, validator_not_empty)
            val: str = prompt_session.prompt(
                HTML(
                    f"<yellow>#tx_builder:internal_txs ></yellow> Parameter #{i + 1} ({typ}): "
                ),
                validator=validator,
                placeholder="",
            )
            param_values.append(val)
        from eth_abi.abi import encode as abi_encode
        from eth_utils import function_signature_to_4byte_selector

        def parse_value(val, typ):
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
            parse_value(v, t) for v, t in zip(param_values, param_types)
        ]
        selector = function_signature_to_4byte_selector(
            f"{func_name}({','.join(param_types)})"
        )
        encoded_args = abi_encode(param_types, parsed_param_values)
        tx_data = selector + encoded_args
    elif tx_type == 2:
        tx_data_hex = prompt_session.prompt(
            HTML("<orange>#tx_builder:internal_txs ></orange> Raw data (hex): "),
            validator=validator_data,
            placeholder=HTML("<grey>e.g. 0x...</grey>"),
        )
        tx_data = to_bytes(hexstr=tx_data_hex)
    return MultiSendTx(
        operation=MultiSendOperation(tx_operation),
        to=tx_to,
        value=int(tx_value),
        data=tx_data,
    )
