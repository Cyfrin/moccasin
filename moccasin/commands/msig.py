from argparse import Namespace

from moccasin.msig_cli.msig_cli import MsigCli
from moccasin.msig_cli.arg_parser import create_msig_parser


# --- Main Function ---
def main(args: Namespace) -> int:
    """Main entry point for the msig CLI."""

    msig_cli = MsigCli()
    return msig_cli.run(args)
