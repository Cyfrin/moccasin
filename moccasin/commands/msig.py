from argparse import Namespace
from moccasin.logging import logger
from msig_cli import tx_builder


def main(args: Namespace) -> int:
    if args.msig_command == "tx":
        tx_builder(args)
    else:
        logger.warning(f"Unknown msig command: {args.msig_command}")
    return 0
