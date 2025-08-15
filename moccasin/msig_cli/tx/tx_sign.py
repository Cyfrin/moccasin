from argparse import Namespace
from pathlib import Path
from typing import Optional

from prompt_toolkit import HTML, PromptSession, print_formatted_text
from safe_eth.safe import Safe, SafeTx

from moccasin.moccasin_account import MoccasinAccount
from moccasin.msig_cli.common_prompts import prompt_save_safe_tx_json
from moccasin.msig_cli.tx.sign_prompts import (
    prompt_account_name,
    prompt_account_password,
    prompt_confirm_sign,
    prompt_private_key,
    prompt_sign_with_moccasin_account,
)
from moccasin.msig_cli.utils.helpers import (
    get_custom_eip712_structured_data,
    pretty_print_safe_tx,
    save_safe_tx_json,
)
from moccasin.msig_cli.validators import validate_json_file


# --- Main entrypoint for the tx_sign command ---
def run(
    prompt_session: PromptSession,
    safe_instance: Safe,
    safe_tx: SafeTx,
    signer: Optional[MoccasinAccount],
    output_file_safe_tx: Optional[Path],
) -> SafeTx:
    """Main entrypoint for the tx_sign command."""
    # Check if the account address is one of the Safe owners
    if not safe_instance.retrieve_is_owner(signer.address):
        raise ValueError(
            f"Signer account {signer.address} is not one of the Safe owners. Cannot proceed with signing."
        )

    # Check if signer has already signed the SafeTx
    print(safe_tx.signers)
    if signer.address in safe_tx.signers:
        raise ValueError(
            f"Signer account {signer.address} has already signed the SafeTx. Cannot proceed with signing."
        )

    # Display the SafeTx details
    pretty_print_safe_tx(safe_tx)
    # Ask for user confirmation to sign the SafeTx
    confirm = prompt_confirm_sign(prompt_session)
    # If user declines, abort signing
    if confirm.lower() not in ("yes", "y"):
        raise ValueError("User aborted tx_sign command.")

    # Sign the SafeTx
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

    # Save EIP-712 structured data as JSON
    safe_tx_data = get_custom_eip712_structured_data(safe_tx)
    if output_file_safe_tx is None:
        output_file_safe_tx = prompt_save_safe_tx_json(prompt_session)

    if output_file_safe_tx is not None:
        save_safe_tx_json(output_file_safe_tx, safe_tx_data)
    else:
        print_formatted_text(HTML("<b><yellow>Not saving EIP-712 JSON.</yellow></b>"))

    return safe_tx


# --- Tx build helper functions ---
def preprocess_raw_args(args: Namespace) -> tuple[Optional[Path], Optional[Path]]:
    """Preprocess raw arguments for tx_sign command."""
    input_json = getattr(args, "input_json", None)
    output_json = getattr(args, "output_json", None)

    if input_json is not None:
        input_json = validate_json_file(args.input_json)
    if output_json is not None:
        output_json = validate_json_file(args.output_json)

    return input_json, output_json


# --- Tx sign helper functions ---
def get_signer_account(prompt_session: PromptSession) -> MoccasinAccount:
    """Get the signer account for the transaction."""
    account = None
    # Ask user if they want to sign with a Moccasin account
    is_mox_account = prompt_sign_with_moccasin_account(prompt_session)
    if is_mox_account.lower() in ("yes", "y"):
        account_name = prompt_account_name(prompt_session)
        password = prompt_account_password(prompt_session)
        account = MoccasinAccount(
            keystore_path_or_account_name=account_name, password=password
        )
    else:
        # Prompt for private key if not using Moccasin account
        private_key = prompt_private_key(prompt_session)
        account = MoccasinAccount(private_key=private_key)

    return account
