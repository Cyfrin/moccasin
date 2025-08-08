import json

from eth_utils import to_checksum_address
from prompt_toolkit import HTML, print_formatted_text

from moccasin.msig_cli.constants import LEFT_PROMPT_SIGN
from moccasin.msig_cli.validators import (
    validator_safe_address,
    validator_not_empty,
    validator_rpc_url,
    validator_json_file,
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


def prompt_continue_next_step(prompt_session, next_cmd):
    answer = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Continue to {next_cmd}? (c/q):</b> "),
        placeholder=HTML("<grey>c/q, y/n</grey>"),
        validator=validator_not_empty,
    )
    return True if answer.strip().lower() in ("c", "continue", "y", "yes") else False


def prompt_save_safe_tx_json(prompt_session, safe_tx_data, json_output=None):
    if json_output:
        with open(json_output, "w") as f:
            json.dump(safe_tx_data, f, indent=2, default=str)
        print_formatted_text(
            HTML(f"<b><green>Saved EIP-712 JSON:</green> {json_output}</b>")
        )
        return
    save = prompt_session.prompt(
        HTML(f"{LEFT_PROMPT_SIGN}<b>Save EIP-712 JSON? (y/n): </b>"),
        placeholder=HTML("<grey>y/n</grey>"),
        validator=validator_not_empty,
    )
    if save.strip().lower() in ("y", "yes"):
        filename = prompt_session.prompt(
            HTML(f"{LEFT_PROMPT_SIGN}<b>Filename for EIP-712 JSON? </b>"),
            placeholder=HTML("<grey>./safe-tx.json</grey>"),
            validator=validator_json_file,
        )
        with open(filename, "w") as f:
            json.dump(safe_tx_data, f, indent=2, default=str)
        print_formatted_text(
            HTML(f"<b><green>Saved EIP-712 JSON:</green> {filename}</b>")
        )
    else:
        print_formatted_text(HTML("<b><yellow>Not saving EIP-712 JSON.</yellow></b>"))
