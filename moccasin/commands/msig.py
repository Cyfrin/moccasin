import traceback
from argparse import Namespace

from prompt_toolkit import HTML, print_formatted_text

from moccasin.msig_cli.msig_cli import MsigCli
from moccasin.msig_cli.utils.exceptions import MsigCliError, MsigCliUserAbort


# --- Main Function ---
def main(args: Namespace) -> int:
    """Main entry point for the msig CLI."""

    msig_cli = MsigCli()

    try:
        msig_cli.run(args)
        print_formatted_text(
            HTML("<b><green>msig CLI completed successfully.</green></b>")
        )
        # Return 0 for successful completion
        print_formatted_text(HTML("<b><cyan>Shutting down msig CLI...</cyan></b>"))
        return 0
    # @TODO: fine tune error message from subcommands and printing display
    except MsigCliUserAbort as e:
        print_formatted_text(HTML(f"<b><red>*** {e} ***</red></b>"))
        return 130
    except MsigCliError as e:
        print_formatted_text(HTML(f"<b><red>!!! {e} !!!</red></b>"))
        return 1
    except Exception as e:
        print_formatted_text(HTML(f"<b><red>!!! Unexpected error: {e} !!!</red></b>"))
        traceback.print_exc()
        return 1
    return 0
