from argparse import Namespace

from eth import constants

ALIAS_TO_COMMAND = {
    "zero-address": "zero",
    "zero_address": "zero",
    "address-zero": "zero",
    "address_zero": "zero",
}


def main(args: Namespace) -> int:
    command = args.utils_command.strip().lower()
    utils_command = ALIAS_TO_COMMAND.get(command, command)
    if utils_command.strip().lower() == "zero":
        print("0x" + constants.ZERO_ADDRESS.hex())
    return 0
