"""Colored help output for the Moccasin CLI."""

import argparse
import sys

BANNER = (
    " __  __                         _\n"
    "|  \\/  | ___   ___ ___ __ _ ___(_)_ __\n"
    "| |\\/| |/ _ \\ / __/ __/ _` / __| | '_ \\\n"
    "| |  | | (_) | (_| (_| (_| \\__ \\ | | | |\n"
    "|_|  |_|\\___/ \\___\\___\\__,_|___/_|_| |_|"
)

MOCCASIN_ORANGE = "rgb(255,165,0)"


def _render_help(parser: argparse.ArgumentParser, *, show_banner: bool = False) -> None:
    """Print parser help with optional colored banner and styled text.

    Falls back to plain argparse output for non-TTY or if rich is unavailable.
    """
    if not sys.stdout.isatty():
        argparse.ArgumentParser.print_help(parser)
        return

    try:
        from rich.console import Console
        from rich.text import Text

        console = Console(highlight=False)

        if show_banner:
            banner_text = Text(BANNER, style=f"bold {MOCCASIN_ORANGE}")
            console.print(banner_text)
            console.print()

        help_text = parser.format_help()
        text = Text(help_text)

        text.highlight_regex(r"(?m)^usage:", style=f"bold {MOCCASIN_ORANGE}")
        text.highlight_regex(r"(?m)^[a-z][\w ]+:$", style=f"bold {MOCCASIN_ORANGE}")
        text.highlight_regex(r"(?m)^    \w[\w-]*", style=MOCCASIN_ORANGE)
        text.highlight_regex(r"(?m)^  -[\w-]+(?:, --[\w-]+)?", style=MOCCASIN_ORANGE)
        text.highlight_regex(r"(?m)^  --[\w-]+", style=MOCCASIN_ORANGE)

        console.print(text)
    except ImportError:
        argparse.ArgumentParser.print_help(parser)


class MoccasinParser(argparse.ArgumentParser):
    """ArgumentParser subclass with rich-formatted help output."""

    show_banner: bool = False

    def print_help(self, file=None) -> None:
        if file is None:
            _render_help(self, show_banner=self.show_banner)
        else:
            super().print_help(file)
