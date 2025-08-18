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

from moccasin.moccasin_account import MoccasinAccount
from moccasin.msig_cli.tx.broadcast_prompts import (
    prompt_account_name,
    prompt_account_password,
    prompt_broadcast_with_moccasin_account,
    prompt_confirm_base_gas_limit,
    prompt_confirm_broadcast,
    prompt_confirm_safe_tx_gas_limit,
    prompt_private_key,
)
from moccasin.msig_cli.utils.helpers import pretty_print_safe_tx
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

    # Estimate the gas for the SafeTx
    safe_tx_gas = None
    try:
        safe_tx_gas = safe_instance.estimate_tx_gas(
            safe_tx.to, safe_tx.value, safe_tx.data, safe_tx.operation
        )
    except Exception as e:
        raise Exception(f"Error estimating gas for SafeTx: {e}") from e

    print_formatted_text(
        HTML(f"<b><green>Estimated gas for SafeTx: {safe_tx_gas}</green></b>")
    )

    # Compare the gas estimate with the SafeTx gas limit
    if safe_tx.safe_tx_gas < safe_tx_gas:
        print_formatted_text(
            HTML(
                f"<b><red>Warning: SafeTx gas limit ({safe_tx.safe_tx_gas}) is less than the estimated gas ({safe_tx_gas}).</red></b>"
            )
        )
        # Ask user if they want to change the gas limit or continue with the current gas limit
        confirm = prompt_confirm_safe_tx_gas_limit(prompt_session, safe_tx_gas)
        if confirm.lower() in ("yes", "y"):
            safe_tx.safe_tx_gas = safe_tx_gas
            print_formatted_text(
                HTML(
                    f"<b><green>SafeTx gas limit updated to: {safe_tx.safe_tx_gas}</green></b>"
                )
            )
        else:
            print_formatted_text(
                HTML(
                    f"<b><yellow>Continuing with current SafeTx gas limit: {safe_tx.safe_tx_gas}</yellow></b>"
                )
            )

    # Get the base gas for the Safe trnsaction
    base_gas = None
    try:
        base_gas = safe_instance.estimate_tx_base_gas(
            safe_tx.to,
            safe_tx.value,
            safe_tx.data,
            safe_tx.operation,
            safe_tx.gas_token,
            safe_tx.safe_tx_gas,
        )
    except Exception as e:
        raise Exception(f"Error estimating base gas for SafeTx: {e}") from e
    print_formatted_text(
        HTML(f"<b><green>Estimated base gas for SafeTx: {base_gas}</green></b>")
    )

    # Compare the base gas with the SafeTx base gas
    if safe_tx.base_gas < base_gas:
        print_formatted_text(
            HTML(
                f"<b><red>Warning: SafeTx base gas ({safe_tx.base_gas}) is less than the estimated base gas ({base_gas}).</red></b>"
            )
        )
        # Ask user if they want to change the base gas or continue with the current base gas
        confirm = prompt_confirm_base_gas_limit(prompt_session, base_gas)
        if confirm.lower() in ("yes", "y"):
            safe_tx.base_gas = base_gas
            print_formatted_text(
                HTML(
                    f"<b><green>SafeTx base gas updated to: {safe_tx.base_gas}</green></b>"
                )
            )
        else:
            print_formatted_text(
                HTML(
                    f"<b><yellow>Continuing with current SafeTx base gas: {safe_tx.base_gas}</yellow></b>"
                )
            )

    # Update the gas price if not set
    if safe_tx.gas_price is None:
        print_formatted_text(
            HTML(
                "<b><yellow>SafeTx gas price is not set. Using eth client's gas price.</yellow></b>"
            )
        )
        # Use the Safe's gas price if not set in the SafeTx
        # see: safe_tx execute method
        safe_tx.gas_price = safe_instance.w3.eth.gas_price
        print_formatted_text(
            HTML(f"<b><green>SafeTx gas price set to: {safe_tx.gas_price}</green></b>")
        )

    # Check if the Safe has enough funds for the gas
    if not safe_instance.check_funds_for_tx_gas(
        safe_tx.safe_tx_gas, safe_tx.base_gas, safe_tx.gas_price, safe_tx.gas_token
    ):
        raise ValueError(
            "Safe contract does not have enough funds to cover the gas for this transaction."
        )

    # Display the SafeTx details
    pretty_print_safe_tx(safe_tx)

    # Ask for user confirmation to boradcast the SafeTx
    confirm = prompt_confirm_broadcast(prompt_session)
    # If user declines, abort signing
    if confirm.lower() not in ("yes", "y"):
        raise ValueError("User aborted tx_broadcast command.")

    # Broadcast the SafeTx
    try:
        safe_tx.call(tx_sender_address=broadcaster.address)
        safe_tx.execute(tx_sender_private_key=broadcaster.private_key)
    except Exception as e:
        raise Exception(
            f"Error signing SafeTx with account {broadcaster.address}: {e}"
        ) from e

    print_formatted_text(HTML("<b><green>SafeTx broadcasted successfully!</green></b>"))

    # Display the tx hash and tx params
    print_formatted_text(
        HTML(
            f"<b><green>SafeTx broadcasted with tx hash: {safe_tx.tx_hash}</green></b>"
        )
    )
    print_formatted_text(
        HTML(f"<b><green>SafeTx params: {safe_tx.tx_params}</green></b>")
    )

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
