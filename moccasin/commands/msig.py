from argparse import Namespace

from moccasin.msig_cli.msig_cli import MsigCli


# --- Main Function ---
def main(args: Namespace) -> int:
    """Main entry point for the msig CLI."""

    msig_cli = MsigCli()
    return msig_cli.run(args.msig_command, args)
