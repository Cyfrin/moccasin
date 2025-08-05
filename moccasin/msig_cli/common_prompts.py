import json
from eth_utils import to_checksum_address
from prompt_toolkit import HTML, print_formatted_text

from moccasin.msig_cli.validators import (
    validator_not_empty,
    validator_rpc_url,
    validator_safe_address,
    validator_json_file,
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


def prompt_save_safe_tx_json(prompt_session, safe_tx_data, json_output=None):
    """Prompt user to save EIP-712 structured data as JSON, or save directly if path is given."""
    if json_output:
        with open(json_output, "w") as f:
            json.dump(safe_tx_data, f, indent=2, default=str)
        print_formatted_text(
            HTML(
                f"\n<b><green>EIP-712 structured data saved to:</green></b> {json_output}\n"
            )
        )
        return

    # If no output file is specified, prompt user to save
    save = prompt_session.prompt(
        HTML(
            "\n<orange>Would you like to save the EIP-712 structured data to a .json file? (y/n): </orange>"
        ),
        placeholder=HTML("<grey>y/n, yes/no</grey>"),
        validator=validator_not_empty,
    )
    if save.strip().lower() in ("y", "yes"):
        # Prompt for filename and validate it
        filename = prompt_session.prompt(
            HTML(
                "<orange>Where would you like to save the EIP-712 JSON file? (e.g. ./safe-tx.json): </orange>"
            ),
            placeholder=HTML("<grey>./safe-tx.json</grey>"),
            validator=validator_json_file,
        )
        with open(filename, "w") as f:
            json.dump(safe_tx_data, f, indent=2, default=str)
        print_formatted_text(
            HTML(
                f"\n<b><green>EIP-712 structured data saved to:</green></b> {filename}\n"
            )
        )
    else:
        print_formatted_text(
            HTML("\n<b><yellow>Not saving EIP-712 structured data.</yellow></b>\n")
        )
