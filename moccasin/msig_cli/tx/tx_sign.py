from pathlib import Path
from typing import Optional

from hexbytes import HexBytes
from prompt_toolkit import HTML, PromptSession, print_formatted_text
from safe_eth.safe import Safe, SafeTx

from moccasin.moccasin_account import MoccasinAccount
from moccasin.msig_cli.common_prompts import prompt_save_safe_tx_json
from moccasin.msig_cli.tx.sign_prompts import (
    prompt_account_name,
    prompt_account_password,
    prompt_confirm_sign,
    prompt_is_right_account,
    prompt_private_key,
    prompt_sign_with_moccasin_account,
)
from moccasin.msig_cli.utils.exceptions import MsigCliError, MsigCliUserAbort
from moccasin.msig_cli.utils.helpers import (
    get_eip712_structured_data,
    pretty_print_safe_tx,
)
from moccasin.msig_cli.validators import is_valid_private_key


def run(
    prompt_session: PromptSession,
    safe_instance: Safe,
    safe_tx: SafeTx,
    output_file_safe_tx: Optional[str],
    signer: Optional[str],
) -> SafeTx:
    """Main entrypoint for the tx_sign command."""
    # If signer is not provided, prompt for it
    try:
        # Get input values from args
        sig_output_file_safe_tx = (
            Path(output_file_safe_tx) if output_file_safe_tx else None
        )
        sig_signer = signer

        # Initialize the signer account
        # If sig_signer is provided, use it; otherwise, prompt for it
        account = None
        if not sig_signer:
            is_mox_account = prompt_sign_with_moccasin_account(prompt_session)
            if is_mox_account.lower() in ("yes", "y"):
                account_name = prompt_account_name(prompt_session)
                password = prompt_account_password(prompt_session)
                try:
                    account = MoccasinAccount(
                        keystore_path_or_account_name=account_name, password=password
                    )
                except MsigCliError as e:
                    raise MsigCliError(
                        f"Error initializing MoccasinAccount with prompted name and password: {e}"
                    ) from e
            else:
                private_key = prompt_private_key(prompt_session)
                try:
                    account = MoccasinAccount(private_key=private_key)
                except Exception as e:
                    raise MsigCliError(
                        f"Error initializing MoccasinAccount with prompted private key: {e}"
                    ) from e
        else:
            # Check if signer is a string name or a private key
            if is_valid_private_key(sig_signer):
                # Initialize MoccasinAccount with private key
                try:
                    account = MoccasinAccount(private_key=HexBytes(sig_signer).hex())
                except Exception as e:
                    raise MsigCliError(
                        f"Error initializing MoccasinAccount with arg private key: {e}"
                    ) from e
            else:
                # Assume signer is an account name and prompt for password
                try:
                    password = prompt_account_password(prompt_session)
                    account = MoccasinAccount(
                        keystore_path_or_account_name=signer, password=password
                    )
                except Exception as e:
                    raise MsigCliError(
                        f"Error initializing MoccasinAccount with arg account name: {e}"
                    ) from e

        # Check if account is initialized
        if account and account.address:
            # Check if the account is the right one
            is_right_account = prompt_is_right_account(prompt_session, account.address)
            if is_right_account.lower() not in ("yes", "y"):
                raise MsigCliUserAbort(
                    "User aborted tx_sign command due to wrong account."
                )
        else:
            # If account is not initialized, raise an error
            raise MsigCliError(
                "Signer account not initialized. Cannot proceed with signing."
            )

        # Display the initialized account
        print_formatted_text(
            HTML(
                f"\n<b><green>Signer account initialized successfully: {account.address}</green></b>\n"
            )
        )

        # Check if the account address is one of the Safe owners
        if not safe_instance.retrieve_is_owner(account.address):
            raise MsigCliError(
                f"Signer account {account.address} is not one of the Safe owners. Cannot proceed with signing."
            )

        # Check if signer has already signed the SafeTx
        if account.address in safe_tx.signers:
            raise MsigCliError(
                f"Signer account {account.address} has already signed the SafeTx. Cannot proceed with signing."
            )

        # Display the SafeTx details
        pretty_print_safe_tx(safe_tx)
        # Ask for user confirmation to sign the SafeTx
        confirm = prompt_confirm_sign(prompt_session)
        # If user declines, abort signing
        if confirm.lower() not in ("yes", "y"):
            raise MsigCliUserAbort("User aborted tx_sign command.")

        # Sign the SafeTx
        try:
            safe_tx.sign(private_key=account.private_key.hex())
            print_formatted_text(
                HTML("<b><green>SafeTx signed successfully!</green></b>")
            )
        except Exception as e:
            raise MsigCliError(
                f"Error signing SafeTx with account {account.address}: {e}"
            ) from e

        # Display the ordered signers
        # Note: SafeTx.sorted_signers returns the most recent signers first
        ordered_signers = list(reversed(safe_tx.sorted_signers))
        for idx, sig in enumerate(ordered_signers, start=1):
            print_formatted_text(
                HTML(f"<b><green>SafeTx signer {idx}: {sig}</green></b>")
            )

        # Save EIP-712 structured data as JSON
        safe_tx_data = get_eip712_structured_data(safe_tx)
        prompt_save_safe_tx_json(prompt_session, safe_tx_data, sig_output_file_safe_tx)

        return safe_tx

    # If any error occurs, raise an appropriate exception
    except MsigCliError as e:
        raise MsigCliError(f"Signing failed: {e}") from e
    except MsigCliUserAbort as e:
        raise MsigCliUserAbort(f"User aborted signing: {e}") from e
    except Exception as e:
        raise Exception(f"Unexpected error during signing: {e}") from e
