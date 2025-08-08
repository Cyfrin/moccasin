from pathlib import Path

from prompt_toolkit import HTML
from prompt_toolkit.shortcuts import print_formatted_text

from moccasin.msig_cli.constants import LEFT_PROMPT_SIGN
from moccasin.msig_cli.validators import (
    validator_not_empty,
    validator_private_key,
    validator_json_file,
)


def prompt_sign_with_moccasin_account(prompt_session):
    return prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Sign with MoccasinAccount? </b>"),
        placeholder=HTML("<grey>yes/no</grey>"),
        validator=validator_not_empty,
    )


def prompt_account_name(prompt_session):
    return prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Account name? </b>"),
        placeholder=HTML("<grey>name</grey>"),
        validator=validator_not_empty,
    )


def prompt_account_password(prompt_session):
    return prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Account password? </b>"),
        placeholder=HTML("<grey>*******</grey>"),
        is_password=True,
        validator=validator_not_empty,
    )


def prompt_private_key(prompt_session):
    print_formatted_text(
        HTML(
            f"{LEFT_PROMPT_SIGN}<b><red>Signing with private key is discouraged.</red></b>"
        )
    )
    return prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Private key? </b>"),
        placeholder=HTML("<grey>0x...</grey>"),
        is_password=True,
        validator=validator_private_key,
    )


def prompt_is_right_account(prompt_session, address):
    return prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Right account {address}? </b>"),
        placeholder=HTML("<grey>yes/no</grey>"),
        validator=validator_not_empty,
        is_password=False,
    )


def prompt_confirm_sign(prompt_session):
    return prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Sign this SafeTx? </b>"),
        placeholder=HTML("<grey>yes/no</grey>"),
        validator=validator_not_empty,
    )


def prompt_eip712_input_file(prompt_session):
    return Path(
        prompt_session.prompt(
            HTML(f"{LEFT_PROMPT_SIGN}<b>EIP-712 input file? </b>"),
            validator=validator_json_file,
            placeholder=HTML("<grey>./input.json</grey>"),
        )
    )
