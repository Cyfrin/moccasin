from pathlib import Path

from eth_utils import to_checksum_address
from prompt_toolkit import HTML

from moccasin.msig_cli.constants import LEFT_PROMPT_SIGN
from moccasin.msig_cli.validators import (
    validator_json_file,
    validator_not_empty,
    validator_rpc_url,
    validator_safe_address,
)


def prompt_rpc_url(prompt_session):
    return prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>RPC URL? </b>"), validator=validator_rpc_url
    )


def prompt_safe_address(prompt_session):
    """Prompt the user for the Safe address."""
    return to_checksum_address(
        prompt_session.prompt(
            HTML(f"{LEFT_PROMPT_SIGN}<b>Safe address? </b>"),
            validator=validator_safe_address,
        )
    )


def prompt_eip712_input_file(prompt_session):
    return Path(
        prompt_session.prompt(
            HTML(f"{LEFT_PROMPT_SIGN}<b>EIP-712 input file? </b>"),
            validator=validator_json_file,
            placeholder=HTML("<grey>./input.json</grey>"),
        )
    )


def prompt_confirm_proceed(prompt_session, message: str):
    return prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>{message} </b>"),
        placeholder=HTML("<grey>y/n, yes/no</grey>"),
        validator=validator_not_empty,
    )


def prompt_save_safe_tx_json(prompt_session):
    save = prompt_confirm_proceed(prompt_session, "Save EIP-712 JSON to file?")
    if save.strip().lower() in ("y", "yes"):
        filename = prompt_session.prompt(
            HTML(f"{LEFT_PROMPT_SIGN}<b>Filename for EIP-712 JSON? </b>"),
            placeholder=HTML("<grey>./safe-tx.json</grey>"),
            validator=validator_json_file,
        )
        return filename
    else:
        return None
