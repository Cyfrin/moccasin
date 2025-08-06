from pathlib import Path

from prompt_toolkit import HTML
from prompt_toolkit.shortcuts import print_formatted_text

from moccasin.msig_cli.validators import (
    validator_not_empty,
    validator_private_key,
    validator_json_file,
)


def prompt_sign_with_moccasin_account(prompt_session):
    """Prompt user if they want to sign with a MoccasinAccount."""
    return prompt_session.prompt(
        HTML(
            "<b><orange>#tx_sign > </orange>Do you want to sign with a MoccasinAccount? (yes/no): </b>"
        ),
        placeholder=HTML("<b><grey>yes/no</grey></b>"),
        validator=validator_not_empty,
    )


def prompt_account_name(prompt_session):
    """Prompt for MoccasinAccount name."""
    return prompt_session.prompt(
        HTML(
            "<b><orange>#tx_sign > </orange>What is the name of the MoccasinAccount? </b>"
        ),
        placeholder=HTML("<b><grey>account_name</grey></b>"),
        validator=validator_not_empty,
    )


def prompt_account_password(prompt_session):
    """Prompt for MoccasinAccount password."""
    return prompt_session.prompt(
        HTML(
            "<b><orange>#tx_sign > </orange>What is the password for the MoccasinAccount? </b>"
        ),
        placeholder=HTML("<b><grey>*******</grey></b>"),
        is_password=True,
        validator=validator_not_empty,
    )


def prompt_private_key(prompt_session):
    """Prompt for private key (discouraged)."""
    print_formatted_text(
        HTML(
            "\n<b><red>Signing with private key is discouraged. Please use MoccasinAccount instead.</red></b>\n"
        )
    )
    return prompt_session.prompt(
        HTML(
            "<b><orange>#tx_sign > </orange>What is the private key of the signer? </b>"
        ),
        placeholder=HTML("<b><grey>0x...</grey></b>"),
        is_password=True,
        validator=validator_private_key,
    )


def prompt_is_right_account(prompt_session, address):
    """Prompt user to confirm the account address."""
    return prompt_session.prompt(
        HTML(
            f"<b><orange>#tx_sign > </orange>Is this the right account? {address} (yes/no): </b>"
        ),
        placeholder=HTML("<b><grey>yes/no</grey></b>"),
        validator=validator_not_empty,
        is_password=False,
    )


def prompt_confirm_sign(prompt_session):
    """Prompt user to confirm signing the SafeTx."""
    return prompt_session.prompt(
        HTML(
            "<b><orange>#tx_sign > </orange>Do you want to sign this SafeTx? (yes/no): </b>"
        ),
        placeholder=HTML("<b><grey>yes/no</grey></b>"),
        validator=validator_not_empty,
    )


def prompt_eip712_input_file(prompt_session):
    """Prompt user for EIP-712 input file path and return as Path object."""
    return Path(
        prompt_session.prompt(
            HTML(
                "<b><orange>#tx_sign > </orange>Could not find SafeTx. Please provide EIP-712 input file: </b>"
            ),
            validator=validator_json_file,
            placeholder=HTML("<b><grey>./path/to/eip712_input.json</grey></b>"),
        )
    )
