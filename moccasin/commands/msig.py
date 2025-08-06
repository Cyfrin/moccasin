from argparse import Namespace

from prompt_toolkit import HTML, print_formatted_text

from moccasin.msig_cli.msig_cli import MsigCli
from moccasin.msig_cli.utils import MsigCliError, MsigCliUserAbort


# --- Main Function ---
def main(args: Namespace) -> int:
    """Main entry point for the msig CLI."""

    msig_cli = MsigCli()
    try:
        msig_cli.run(args)
        print_formatted_text(
            HTML("<b><green>msig CLI completed successfully.</green></b>")
        )
    except MsigCliUserAbort as e:
        print_formatted_text(HTML(f"<b><red>*** {e} ***</red></b>"))
        return 130
    except MsigCliError as e:
        print_formatted_text(HTML(f"<b><red>!!! {e} !!!</red></b>"))
        return 1
    except Exception as e:
        print_formatted_text(HTML(f"<b><red>!!! Unexpected error: {e} !!!</red></b>"))
        return 1
    finally:
        print_formatted_text(HTML("<b><cyan>Shutting down msig CLI...</cyan></b>"))

    # Return 0 for successful completion
    return 0
