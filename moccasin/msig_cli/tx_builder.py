import json
from typing import Optional

from eth_typing import ChecksumAddress

from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.shortcuts import clear as prompt_clear

from safe_eth.safe import Safe, SafeTx
from safe_eth.safe.multi_send import MultiSend, MultiSendOperation
from safe_eth.util.util import to_0x_hex_str

from moccasin.logging import logger
from moccasin.msig_cli.utils import GoBackToPrompt
from moccasin.msig_cli.prompts import (
    prompt_safe_nonce,
    prompt_gas_token,
    prompt_internal_txs,
    prompt_single_internal_tx,
)
from moccasin.msig_cli.utils import pretty_print_safe_tx


def handle_multisend_batch(prompt_session, safe_instance, data, to):
    prompt_session = prompt_session
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
        if to and to != multi_send_address:
            print_formatted_text(
                HTML(
                    f"<b><yellow>Warning:</yellow></b> Overriding provided --to address with MultiSend address: {multi_send_address}"
                )
            )
        to = multi_send_address
        print_formatted_text(HTML("<b><magenta>Decoded MultiSend batch:</magenta></b>"))
        for idx, tx in enumerate(decoded_batch, 1):
            print_formatted_text(
                HTML(
                    f"<b>Tx {idx}:</b> operation={tx.operation.name}, to={tx.to}, value={tx.value}, data={tx.data.hex()[:20]}{'...' if len(tx.data) > 10 else ''}"
                )
            )
        confirm = prompt_session.prompt(
            HTML("<orange>Does this batch look correct? (y/n): </orange>"),
            placeholder="y/n, yes/no",
        )
        if confirm.lower() not in ("y", "yes"):
            print_formatted_text(
                HTML(
                    "<b><red>Aborting due to user rejection of decoded batch.</red></b>"
                )
            )
            raise GoBackToPrompt
    elif not to:
        to = prompt_session.prompt(
            HTML("<orange>#tx_builder ></orange> Enter target contract address (to): "),
            placeholder=HTML("<grey>e.g. 0x...</grey>"),
        )
        to = ChecksumAddress(to)
    return to


def save_eip712_json(prompt_session, eip712_struct, eip712_json_out=None):
    from moccasin.msig_cli.validators import validator_json_file, validator_not_empty
    from prompt_toolkit import HTML, print_formatted_text

    if eip712_json_out:
        with open(eip712_json_out, "w") as f:
            json.dump(eip712_struct, f, indent=2, default=str)
        print_formatted_text(
            HTML(
                f"\n<b><green>EIP-712 structured data saved to:</green></b> {eip712_json_out}\n"
            )
        )
    else:
        save = prompt_session.prompt(
            HTML(
                "\n<orange>Save EIP-712 structured data to a .json file? (y/n): </orange>"
            ),
            placeholder="y/n, yes/no",
            validator=validator_not_empty,
        )
        if save.lower() in ("y", "yes"):
            filename = prompt_session.prompt(
                HTML(
                    "<orange>Enter output path with filename (e.g. ./safe-tx.json): </orange>"
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
