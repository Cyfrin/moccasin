import importlib
import sys
from pathlib import Path

import tomllib
from typing import Any, List
from docopt import docopt

from gaboon.utils.levenshtein import levenshtein_norm

import argparse

GAB_VERSION_STRING = "Gaboon v{}"


def main(argv: list) -> int:
    if "--version" in argv or "-v" in argv:
        with open("pyproject.toml", "rb") as f:
            gaboon_data = tomllib.load(f)
            print(GAB_VERSION_STRING.format(gaboon_data["project"]["version"]))
            return 0

    parser = argparse.ArgumentParser(
        prog="Gaboon",
        description="Pythonic Smart Contract Development Framework",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=True,
    )

    parser = argparse.ArgumentParser(
        prog="Gaboon",
        description="Pythonic Smart Contract Development Framework",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=True,
    )
    sub_parsers = parser.add_subparsers(dest="command")

    # Init command
    init_sub_parser = sub_parsers.add_parser("init", help="Initialize a new project.")
    init_sub_parser.add_argument(
        "path",
        help="Path of the new project, defaults to current directory.",
        type=Path,
        default=Path("."),
    )
    init_sub_parser.add_argument(
        "-f",
        "--force",
        required=False,
        help="Overwrite existing project.",
        action="store_true",
    )
    init_sub_parser.set_defaults(func=init)

    # Compile command
    compile_sub_parser = sub_parsers.add_parser("compile", help="Compiles the project.")
    compile_sub_parser.set_defaults(func=compile)

    if len(argv) < 1 or argv[0].startswith("-h") or argv[0].startswith("--help"):
        parser.print_help()

    args = parser.parse_args()
    args.func(args)


def compile(args: List[Any]):
    from gaboon.cli.compile import compile

    compile(args.path)


def init(args: List[Any]):
    from gaboon.cli.init import new_project

    new_project(args.path, args.force)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
