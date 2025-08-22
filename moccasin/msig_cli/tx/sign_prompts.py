from prompt_toolkit import HTML
from prompt_toolkit.shortcuts import print_formatted_text

from moccasin.msig_cli.constants import LEFT_PROMPT_SIGN
from moccasin.msig_cli.validators import validator_not_empty, validator_private_key


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
        HTML("\n<b><red>Signing with private key is discouraged.</red></b>")
    )
    return prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Private key? </b>"),
        placeholder=HTML("<grey>0x...</grey>"),
        is_password=True,
        validator=validator_private_key,
    )
