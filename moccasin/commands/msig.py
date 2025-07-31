from argparse import Namespace

from moccasin.msig_cli.msig_cli import MsigCli


# --- Main Function ---
def main(args: Namespace) -> int:
    """Main entry point for the msig CLI."""

    msig_cli = MsigCli()

    if args.msig_command == "tx":
        # Handle transaction-related commands
        return msig_cli.commands["tx_builder"](args)
    elif args.msig_command == "sign":
        # Handle signing-related commands
        return msig_cli.commands["tx_signer"](args)
    elif args.msig_command == "broadcast":
        # Handle broadcasting-related commands
        return msig_cli.commands["tx_broadcast"](args)
