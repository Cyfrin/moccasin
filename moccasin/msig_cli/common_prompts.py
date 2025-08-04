from eth_utils import to_checksum_address
from prompt_toolkit import HTML

from moccasin.msig_cli.validators import (
    validator_not_empty,
    validator_rpc_url,
    validator_safe_address,
)


def prompt_rpc_url(prompt_session):
    """Prompt the user for the RPC URL."""
    return prompt_session.prompt(
        HTML(
            "<b>What is the RPC URL you want to use to connect to the Ethereum network?: </b>"
        ),
        validator=validator_rpc_url,
    )


def prompt_safe_address(prompt_session):
    """Prompt the user for the Safe address."""
    return to_checksum_address(
        prompt_session.prompt(
            HTML("<b>What is the address of the Safe contract you want to use?: </b>"),
            validator=validator_safe_address,
        )
    )


def prompt_continue_next_step(prompt_session, next_cmd):
    """Prompt the user if they want to continue to the next step or quit."""
    answer = prompt_session.prompt(
        HTML(
            f"<b>Would you like to continue to the next step: <green>{next_cmd}</green>? (c to continue, q to quit): </b>"
        ),
        placeholder=HTML("<grey>e.g. c/q, n/no, y/yes</grey>"),
        validator=validator_not_empty,
    )
    return True if answer.strip().lower() in ("c", "continue", "y", "yes") else False
