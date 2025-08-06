import json
from pathlib import Path
from typing import Optional

from eth_utils import to_checksum_address
from hexbytes import HexBytes
from prompt_toolkit import HTML, PromptSession, print_formatted_text

from moccasin.moccasin_account import MoccasinAccount
from moccasin.msig_cli.common_prompts import prompt_save_safe_tx_json
from moccasin.msig_cli.tx.sign_prompts import (
    prompt_eip712_input_file,
    prompt_sign_with_moccasin_account,
    prompt_account_name,
    prompt_account_password,
    prompt_private_key,
    prompt_is_right_account,
    prompt_confirm_sign,
)
from moccasin.msig_cli.tx.helpers import (
    get_eip712_structured_data,
    get_signatures,
    pretty_print_safe_tx,
)
from moccasin.msig_cli.utils import MsigCliError, MsigCliUserAbort, T_SafeTxData
from moccasin.msig_cli.validators import is_valid_private_key

from safe_eth.safe import Safe, SafeTx


def run(
    prompt_session: PromptSession,
    safe_instance: Safe,
    safe_tx: Optional[SafeTx],
    signer: Optional[str],
    signatures: Optional[str],
    input_file_safe_tx: Optional[str] = None,
    output_file_safe_tx: Optional[str] = None,
) -> SafeTx:
    """Main entrypoint for the tx_sign command."""
    # If signer is not provided, prompt for it
    try:
        # Get input values from args
        sig_safe_tx = safe_tx
        sig_signer = signer
        sig_signatures = signatures
        sig_input_file_safe_tx = (
            Path(input_file_safe_tx) if input_file_safe_tx else None
        )
        sig_output_file_safe_tx = (
            Path(output_file_safe_tx) if output_file_safe_tx else None
        )

        # Initialize the signer account
        # If sig_signer is provided, use it; otherwise, prompt for it
        account: MoccasinAccount = None
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
            if is_valid_private_key(signer):
                # Initialize MoccasinAccount with private key
                try:
                    account = MoccasinAccount(private_key=HexBytes(signer))
                except Exception as e:
                    raise MsigCliError(
                        "Error initializing MoccasinAccount with arg private key: {e}"
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
        if account:
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
        # @TODO: Make a script to deploy local Safe and test with Anvil
        if account.address not in safe_instance.retrieve_owners():
            raise MsigCliError(
                f"Signer account {account.address} is not one of the Safe owners. Cannot proceed with signing."
            )

        # Check if safe_tx is initialized
        if not sig_safe_tx:
            # Check if eip712_input_file is provided, else prompt to get it
            if not sig_input_file_safe_tx:
                eip712_prompted_file = prompt_eip712_input_file(prompt_session)
                if not eip712_prompted_file.exists():
                    print_formatted_text(
                        HTML(
                            f"<b><red>File not found: {sig_input_file_safe_tx}</red></b>"
                        )
                    )
                    raise MsigCliError(
                        f"JSON file SafeTx not found: {eip712_prompted_file}"
                    )
                sig_input_file_safe_tx = eip712_prompted_file

            # Load the JSON file
            try:
                with open(sig_input_file_safe_tx, "r") as f:
                    input_file_raw = f.read()
                    safe_tx_json: T_SafeTxData = json.loads(input_file_raw)
            except FileNotFoundError:
                raise MsigCliError(
                    f"JSON file SafeTx not found while opening: {sig_input_file_safe_tx}"
                )
            except json.JSONDecodeError as e:
                raise MsigCliError(
                    f"Invalid JSON format in file: {sig_input_file_safe_tx} - {e}"
                ) from e

            # Get the required fields from the JSON
            safe_tx_eip712 = None
            message_json = None
            signatures_json = None

            # Check if safeTx field is present, or if it is an EIP-712 JSON
            if not safe_tx_json.get("safeTx", None):
                # If safeTx field is not present, check if it is an EIP-712 JSON
                if (
                    "types" in safe_tx_json
                    and "domain" in safe_tx_json
                    and "message" in safe_tx_json
                ):
                    safe_tx_eip712 = safe_tx_json
                    # If it is an EIP-712 JSON, extract the message but not the signatures
                    message_json = safe_tx_eip712.get("message", None)

                else:
                    raise MsigCliError(
                        f"Invalid JSON format in file: {sig_input_file_safe_tx}. Expected 'safeTx' or EIP-712 format."
                    )
            else:
                # If safeTx field is present, use it
                safe_tx_eip712 = safe_tx_json["safeTx"]
                # Extract the message and signatures from the safeTx field
                message_json = safe_tx_eip712.get("message", None)
                signatures_json = safe_tx_eip712.get("signatures", None)

            # Get the sigmature from:
            # 1. CLI input
            # 2. JSON file
            # 3. Default to empty bytes
            sig_signatures = get_signatures(
                cli_signatures=sig_signatures, json_signatures=signatures_json
            )

            # Create SafeTx
            message_json = safe_tx_eip712.get("message", None)
            if message_json:
                try:
                    # Convert the message to SafeTx
                    sig_safe_tx = safe_instance.build_multisig_tx(
                        to=to_checksum_address(message_json["to"]),
                        value=message_json["value"],
                        data=bytes.fromhex(
                            message_json["data"].lstrip("0x")
                            if message_json["data"].startswith("0x")
                            else message_json["data"]
                        ),
                        operation=message_json["operation"],
                        safe_nonce=message_json["nonce"],
                        safe_tx_gas=message_json["safeTxGas"],
                        base_gas=message_json["baseGas"],
                        gas_price=message_json["gasPrice"],
                        gas_token=to_checksum_address(message_json["gasToken"]),
                        refund_receiver=to_checksum_address(
                            message_json["refundReceiver"]
                        ),
                        signatures=sig_signatures,
                    )
                except Exception as e:
                    print_formatted_text(
                        HTML(f"<b><red>Error creating SafeTx from JSON: {e}</red></b>")
                    )
                    return
            else:
                print_formatted_text(
                    HTML(
                        f"<b><red>Missing 'message' field in 'safeTx' JSON: {sig_input_file_safe_tx}</red></b>"
                    )
                )
                return

        # Prompt the user to validate the SafeTx if it is initialized
        if sig_safe_tx:
            # Display the SafeTx details
            pretty_print_safe_tx(sig_safe_tx)
            # Ask for user confirmation to sign the SafeTx
            confirm = prompt_confirm_sign(prompt_session)
            # If user declines, abort signing
            if confirm.lower() not in ("yes", "y"):
                print_formatted_text(
                    HTML("<b><red>Aborting signing. User declined.</red></b>")
                )
                return
        else:
            # If SafeTx is not initialized, print error and return
            print_formatted_text(
                HTML("<b><red>SafeTx not created. Aborting signing.</red></b>")
            )
            return

        # Sign the SafeTx
        try:
            sig_safe_tx.sign(private_key=account.private_key.hex())
            print_formatted_text(
                HTML("<b><green>SafeTx signed successfully!</green></b>")
            )
        except Exception as e:
            print_formatted_text(HTML(f"<b><red>Error signing SafeTx: {e}</red></b>"))
            return

        # Display the ordered signers
        ordered_signers = sig_safe_tx.sorted_signers
        for idx, sig in enumerate(ordered_signers, start=1):
            print_formatted_text(
                HTML(f"<b><green>SafeTx signer {idx}: {sig}</green></b>")
            )

        # Save EIP-712 structured data as JSON
        safe_tx_data = get_eip712_structured_data(sig_safe_tx)
        prompt_save_safe_tx_json(prompt_session, safe_tx_data, sig_output_file_safe_tx)

        return sig_safe_tx

    # If any error occurs, raise an appropriate exception
    except MsigCliError as e:
        raise MsigCliError(f"Signing failed: {e}") from e
    except MsigCliUserAbort as e:
        raise MsigCliUserAbort(f"User aborted signing: {e}") from e
    except Exception as e:
        raise Exception(f"Unexpected error during signing: {e}") from e
