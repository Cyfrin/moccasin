"""
Prompt helper functions for msig_cli, decoupled from msig_cli state.
"""

import json
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address, to_bytes
from eth.constants import ZERO_ADDRESS
from prompt_toolkit import HTML, print_formatted_text
from moccasin.msig_cli.validators import (
    validator_rpc_url,
    validator_address,
    validator_safe_address,
    validator_number,
    validator_not_zero_number,
    validator_operation,
    validator_data,
    validator_transaction_type,
    validator_function_signature,
    validator_not_empty,
    validator_json_file,
    param_type_validators,
)
from safe_eth.safe.multi_send import MultiSendTx, MultiSendOperation


def prompt_safe_nonce(prompt_session, safe_instance, safe_nonce, cmd):
    if not safe_nonce:
        safe_nonce = prompt_session.prompt(
            HTML(
                f"<orange>#{cmd} ></orange> What nonce should be used for this Safe transaction?: "
            ),
            validator=validator_number,
            placeholder=HTML("<grey>[default: auto retrieval]</grey>"),
        )
        if safe_nonce:
            safe_nonce = int(safe_nonce)
        else:
            safe_nonce = safe_instance.retrieve_nonce()
    return safe_nonce


def prompt_gas_token(prompt_session, gas_token, cmd):
    if not gas_token:
        gas_token = prompt_session.prompt(
            HTML(
                f"<orange>#{cmd} ></orange> What is the gas token address to use for this transaction? (Press Enter to use the default/zero address): "
            ),
            validator=validator_address,
            placeholder=HTML("<grey>[default: 0x...]</grey>"),
        )
        if gas_token:
            gas_token = ChecksumAddress(gas_token)
        else:
            gas_token = to_checksum_address(ZERO_ADDRESS)
    return gas_token


def prompt_internal_txs(prompt_session, single_internal_tx_func, cmd):
    internal_txs = []
    nb_internal_txs = prompt_session.prompt(
        HTML(
            f"<orange>#{cmd} ></orange> How many internal transactions would you like to include in this batch?: "
        ),
        validator=validator_not_zero_number,
        placeholder=HTML("<grey>[default: 1]</grey>"),
    )
    if nb_internal_txs:
        nb_internal_txs = int(nb_internal_txs)
    else:
        nb_internal_txs = 1
    for idx in range(nb_internal_txs):
        internal_txs.append(
            single_internal_tx_func(prompt_session, idx, nb_internal_txs, cmd)
        )
    return internal_txs


def prompt_single_internal_tx(prompt_session, idx, nb_internal_txs, cmd):
    print_formatted_text(
        HTML(
            f"\n\t<b><magenta>--- Internal Transaction {str(idx + 1).zfill(2)}/{str(nb_internal_txs).zfill(2)} ---</magenta></b>\n"
        )
    )
    tx_type = prompt_session.prompt(
        HTML(
            f"<orange>#{cmd}:internal_txs ></orange> What type of internal transaction is this? (0 = call contract, 1 = ERC20 transfer, 2 = raw data): "
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
            HTML(
                f"<orange>#{cmd}:internal_txs ></orange> What is the contract address for this call?: "
            ),
            validator=validator_address,
            placeholder=HTML("<grey>[default: 0x...]</grey>"),
        )
        tx_to = ChecksumAddress(tx_to) if tx_to else to_checksum_address(ZERO_ADDRESS)
        tx_value = prompt_session.prompt(
            HTML(
                f"<orange>#{cmd}:internal_txs ></orange> How much value (in wei) should be sent with this call?: "
            ),
            validator=validator_number,
            placeholder=HTML("<grey>[default: 0]</grey>"),
        )
        tx_value = int(tx_value) if tx_value else 0
        tx_operation = prompt_session.prompt(
            HTML(
                f"<orange>#{cmd}:internal_txs ></orange> What operation type should be used with this call? (0 = call, 1 = delegate call): "
            ),
            validator=validator_operation,
            placeholder=HTML("<grey>[default: 0 for call]</grey>"),
        )
        tx_operation = int(tx_operation) if tx_operation else 0
        function_signature: str = prompt_session.prompt(
            HTML(
                f"<orange>#{cmd}:internal_txs ></orange> What is the function signature for this call? (e.g. transfer(address,uint256)): "
            ),
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
                    f"<yellow>#{cmd}:internal_txs ></yellow> What value should be used for parameter #{i + 1} of type {typ}?: "
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
            HTML(
                f"<orange>#{cmd}:internal_txs ></orange> What is the raw data (hex) for this transaction?: "
            ),
            validator=validator_data,
            placeholder=HTML("<grey>e.g. 0x...</grey>"),
        )
        tx_data = to_bytes(hexstr=tx_data_hex)
    return MultiSendTx(
        operation=MultiSendOperation.CALL.value
        if tx_operation == 0
        else MultiSendOperation.DELEGATE_CALL.value,
        to=tx_to,
        value=int(tx_value),
        data=tx_data,
    )


def prompt_multisend_batch_confirmation(
    prompt_session, decoded_batch, multi_send_address, to
):
    """Prompt user to confirm decoded MultiSend batch and handle address override warning."""
    from prompt_toolkit import HTML, print_formatted_text

    if to and to != multi_send_address:
        print_formatted_text(
            HTML(
                f"<b><red>Warning:</red></b> The provided target address will be overridden with the MultiSend contract address: {multi_send_address}."
            )
        )
    print_formatted_text(
        HTML(
            "<b><magenta>Here is the decoded MultiSend batch. Does everything look correct to you?: </magenta></b>"
        )
    )
    for idx, tx in enumerate(decoded_batch, 1):
        print_formatted_text(
            HTML(
                f"<b>Tx {idx}:</b>\n"
                f"\t  <b><orange>operation:</orange></b> {tx.operation.name}\n"
                f"\t  <b><orange>to:</orange></b> {tx.to}\n"
                f"\t  <b><orange>value:</orange></b> {tx.value}\n"
                f"\t  <b><orange>data:</orange></b> {'0x' + tx.data.hex()}\n"
            )
        )
    confirm = prompt_session.prompt(
        HTML("<orange>Would you like to proceed with this batch? (y/n): </orange>"),
        placeholder="y/n, yes/no",
        validator=validator_not_empty,
    )
    return confirm.strip().lower() in ("y", "yes")


def prompt_target_contract_address(prompt_session):
    """Prompt user for the target contract address if not provided."""
    return prompt_session.prompt(
        HTML(
            "<orange>Could you provide the target contract address for this transaction?: </orange> "
        ),
        placeholder=HTML("<grey>e.g. 0x...</grey>"),
        validator=validator_address,
    )


def prompt_operation_type(prompt_session):
    """Prompt user for the operation type, defaulting to CALL if no delegate call is present."""
    operation = prompt_session.prompt(
        HTML(
            "<orange>What operation type should be used with this call? (0 = call, 1 = delegate call): </orange>"
        ),
        validator=validator_operation,
        placeholder=HTML("<grey>[default: 0 for call]</grey>"),
    )

    return int(operation) if operation else int(MultiSendOperation.CALL.value)


def prompt_save_eip712_json(prompt_session, eip712_struct, eip712_json_out=None):
    """Prompt user to save EIP-712 structured data as JSON, or save directly if path is given."""
    if eip712_json_out:
        with open(eip712_json_out, "w") as f:
            json.dump(eip712_struct, f, indent=2, default=str)
        print_formatted_text(
            HTML(
                f"\n<b><green>EIP-712 structured data saved to:</green></b> {eip712_json_out}\n"
            )
        )
        return
    save = prompt_session.prompt(
        HTML(
            "\n<orange>Would you like to save the EIP-712 structured data to a .json file? (y/n): </orange>"
        ),
        placeholder="y/n, yes/no",
        validator=validator_not_empty,
    )
    if save.strip().lower() in ("y", "yes"):
        filename = prompt_session.prompt(
            HTML(
                "<orange>Where would you like to save the EIP-712 JSON file? (e.g. ./safe-tx.json): </orange>"
            ),
            placeholder="./safe-tx.json",
            validator=validator_json_file,
        )
        with open(filename, "w") as f:
            json.dump(eip712_struct, f, indent=2, default=str)
        print_formatted_text(
            HTML(
                f"\n<b><green>EIP-712 structured data saved to:</green></b> {filename}\n"
            )
        )
    else:
        print_formatted_text(
            HTML("\n<b><yellow>Not saving EIP-712 structured data.</yellow></b>\n")
        )


def prompt_continue_next_step(prompt_session, next_cmd):
    """Prompt the user if they want to continue to the next step or quit."""
    answer = prompt_session.prompt(
        HTML(
            f"<b>Would you like to continue to the next step: <green>{next_cmd}</green>? (c to continue, q to quit): </b>"
        ),
        placeholder="e.g. c/q, n/no, y/yes",
        validator=validator_not_empty,
    )
    return answer.strip().lower()


def prompt_rpc_url(prompt_session):
    """Prompt the user for the RPC URL."""
    return prompt_session.prompt(
        HTML(
            "<b>What is the RPC URL you want to use to connect to the Ethereum network?: </b>"
        ),
        validator=validator_rpc_url,
    )


def prompt_safe_address(prompt_session):
    """Prompt the user for the Safe address."""
    return prompt_session.prompt(
        HTML("<b>What is the address of the Safe contract you want to use?: </b>"),
        validator=validator_safe_address,
    )
