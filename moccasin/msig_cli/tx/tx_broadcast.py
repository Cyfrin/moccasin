"""
safe.estimate_tx_gas
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
    prompt_confirm_broadcast,
    prompt_confirm_gas_limit,
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
    gas_estimate = None
    try:
        gas_estimate = safe_instance.estimate_tx_gas(
            safe_tx.to, safe_tx.value, safe_tx.data, safe_tx.operation
        )
    except Exception as e:
        raise Exception(f"Error estimating gas for SafeTx: {e}") from e

    print_formatted_text(
        HTML(f"<b><green>Estimated gas for SafeTx: {gas_estimate}</green></b>")
    )

    # Compare the gas estimate with the SafeTx gas limit
    if safe_tx.base_gas < gas_estimate:
        print_formatted_text(
            HTML(
                f"<b><red>Warning: SafeTx gas limit ({safe_tx.base_gas}) is less than the estimated gas ({gas_estimate}).</red></b>"
            )
        )
        # Ask user if they want to change the gas limit or continue with the current gas limit
        confirm = prompt_confirm_gas_limit(prompt_session, gas_estimate)
        if confirm.lower() in ("yes", "y"):
            safe_tx.base_gas = gas_estimate
            print_formatted_text(
                HTML(
                    f"<b><green>SafeTx gas limit updated to: {safe_tx.base_gas}</green></b>"
                )
            )
        else:
            print_formatted_text(
                HTML(
                    f"<b><yellow>Continuing with current SafeTx gas limit: {safe_tx.base_gas}</yellow></b>"
                )
            )

    # @XXX: see how to estimate balances, gas price etc... START HERE

    # Display the SafeTx details
    pretty_print_safe_tx(safe_tx)

    # Ask for user confirmation to boradcast the SafeTx
    confirm = prompt_confirm_broadcast(prompt_session)
    # If user declines, abort signing
    if confirm.lower() not in ("yes", "y"):
        raise ValueError("User aborted tx_broadcast command.")

    # Broadcast the SafeTx
    try:
        safe_tx.sign(private_key=signer.private_key.hex())
        print_formatted_text(HTML("<b><green>SafeTx signed successfully!</green></b>"))
    except Exception as e:
        raise Exception(
            f"Error signing SafeTx with account {signer.address}: {e}"
        ) from e

    # Display the ordered signers
    # Note: SafeTx.sorted_signers returns the most recent signers first
    ordered_signers = list(reversed(safe_tx.sorted_signers))
    for idx, sig in enumerate(ordered_signers, start=1):
        print_formatted_text(HTML(f"<b><green>SafeTx signer {idx}: {sig}</green></b>"))

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
    is_mox_account = prompt_sign_with_moccasin_account(prompt_session)
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
