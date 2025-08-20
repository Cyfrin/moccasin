"""
safe.estimate_tx_gas
safe.estimate_tx_base_gas
safe.check_funds_for_tx_gas
safe.send_multisig_tx
"""

from argparse import Namespace
from pathlib import Path
from typing import Optional

from prompt_toolkit import HTML, PromptSession, print_formatted_text
from safe_eth.safe import Safe, SafeTx
from safe_eth.safe.exceptions import InvalidInternalTx

from moccasin.moccasin_account import MoccasinAccount
from moccasin.msig_cli.tx.broadcast_prompts import (
    prompt_account_name,
    prompt_account_password,
    prompt_broadcast_with_moccasin_account,
    prompt_confirm_broadcast,
    prompt_private_key,
)
from moccasin.msig_cli.utils.helpers import (
    get_decoded_tx_data,
    is_multisend_tx,
    pretty_print_broadcasted_tx,
    pretty_print_decoded_multisend,
    pretty_print_safe_tx,
)
from moccasin.msig_cli.validators import validate_json_file


# --- Main entrypoint for the tx_broadcast command ---
def run(
    prompt_session: PromptSession,
    safe_instance: Safe,
    safe_tx: SafeTx,
    broadcaster: MoccasinAccount,
) -> SafeTx:
    """Main entrypoint for the tx_broadcast command."""
    # Check if the SafeTx has not been broadcasted yet
    if safe_tx.tx is not None or safe_tx.tx_hash is not None:
        raise ValueError(
            "SafeTx has already been broadcasted. Cannot broadcast it again."
        )

    # Check if the SafeTx has enough signers
    if len(safe_tx.signers) < safe_instance.retrieve_threshold():
        raise ValueError(
            f"SafeTx requires at least {safe_instance.retrieve_threshold()} signers, but only {len(safe_tx.signers)} signers are provided."
        )

    # Check if safe contract balance is not zero
    if safe_instance.ethereum_client.get_balance(safe_instance.address) <= 0:
        # @FIXME erc20 balance check
        # safe_tx.gas_token is not None
        # and safe_tx.gas_token != ZERO_ADDRESS
        # and safe_instance.ethereum_client.erc20.get_balance(
        #     safe_instance.address, safe_tx.gas_token
        # )
        # <= 0
        raise ValueError(
            "Safe contract does not have any funds. Please fund the Safe contract before broadcasting the transaction."
        )

    # Check if the Safe has enough funds for the gas
    if not safe_instance.check_funds_for_tx_gas(
        safe_tx.safe_tx_gas, safe_tx.base_gas, safe_tx.gas_price, safe_tx.gas_token
    ):
        raise ValueError(
            "Safe contract does not have enough funds to cover the gas for this transaction."
        )

    # Display cost in wei
    estimated_cost_in_wei = (safe_tx.safe_tx_gas + safe_tx.base_gas) * safe_tx.gas_price
    if estimated_cost_in_wei > 0:
        print_formatted_text(
            HTML(
                f"<b><orange>Estimated cost for SafeTx: </orange></b>{estimated_cost_in_wei} wei"
            )
        )
    else:
        print_formatted_text(
            HTML("<b><yellow>Warning: Estimated cost for SafeTx is zero.</yellow></b>")
        )

    # Display the SafeTx details
    pretty_print_safe_tx(safe_tx)

    # Display internal txs if MultiSend batch is present
    if is_multisend_tx(safe_tx.to):
        decoded_batch = get_decoded_tx_data(safe_tx.data)
        if decoded_batch is not None:
            pretty_print_decoded_multisend(decoded_batch)

    # Ask for user confirmation to boradcast the SafeTx
    confirm = prompt_confirm_broadcast(prompt_session)
    # If user declines, abort signing
    if confirm.lower() not in ("yes", "y"):
        raise ValueError("User aborted tx_broadcast command.")

    # Broadcast the SafeTx
    try:
        safe_tx.call(tx_sender_address=broadcaster.address)
        safe_tx.execute(tx_sender_private_key=broadcaster.private_key.hex())
    except InvalidInternalTx:
        raise ValueError(
            "SafeTx contains invalid internal transactions. Please check the transaction data."
        )
    except Exception as e:
        raise Exception(
            f"Error broadcasting SafeTx with account {broadcaster.address}: {e}"
        ) from e

    # Check if the SafeTx was successfully broadcasted
    if safe_tx.tx_hash is None:
        raise ValueError(
            "SafeTx hash is None, something went wrong during broadcasting."
        )

    # Display SafeTx hash
    print_formatted_text(
        HTML("\n<b><green>SafeTx broadcasted successfully!</green></b>")
    )
    print_formatted_text(
        HTML(f"<b><orange>SafeTx hash: </orange></b>{safe_tx.tx_hash.hex()}")
    )

    # Check Broadcasted SafeTx details are available
    if safe_tx.tx is None:
        raise ValueError(
            "SafeTx details are not available after broadcasting. Please check the transaction on the blockchain."
        )
    # Pretty print the broadcasted SafeTx details
    pretty_print_broadcasted_tx(safe_tx.tx)

    return safe_tx


# --- Tx broadcast helper functions ---
def preprocess_raw_args(
    args: Namespace | None,
) -> tuple[Optional[Path], Optional[Path]]:
    """Preprocess raw arguments for tx_sign command."""
    if args is None:
        return None, None

    input_json = getattr(args, "input_json", None)
    output_json = getattr(args, "output_json", None)

    if input_json is not None:
        input_json = validate_json_file(args.input_json)
    if output_json is not None:
        output_json = validate_json_file(args.output_json)

    return input_json, output_json


# --- Tx broadcast helper functions ---
def get_broadcaster_account(prompt_session: PromptSession) -> MoccasinAccount:
    """Get the broadcaster account for the transaction."""
    broadcaster = None
    # Ask user if they want to sign with a Moccasin account
    is_mox_account = prompt_broadcast_with_moccasin_account(prompt_session)
    if is_mox_account.lower() in ("yes", "y"):
        account_name = prompt_account_name(prompt_session)
        password = prompt_account_password(prompt_session)
        broadcaster = MoccasinAccount(
            keystore_path_or_account_name=account_name, password=password
        )
    else:
        # Prompt for private key if not using Moccasin account
        private_key = prompt_private_key(prompt_session)
        broadcaster = MoccasinAccount(private_key=private_key)

    return broadcaster
