import sys
from pathlib import Path
from docopt import docopt
from gaboon.utils.levenshtein import levenshtein_norm
import tomllib
import importlib

__doc__ = """Usage: gab <command> [<args...>] [options <args>]

Commands:
    init        Create a new project with starting folders.
    compile     Compile the contract source files.
    run         Run a python script with config context.
    wallet      Manage your wallets.
    test        Run tests.
    install     Install a package from GitHub.

Options:
    -h --help   Show this screen.
    --version   Show version.

Type `gab <command> --help` for more information on a specific command.
"""

GAB_VERSION_STRING = "Gaboon v{}"


def main(argv: list) -> int:
    if "--version" in argv or "-v" in argv:
        with open("pyproject.toml", "rb") as f:
            gaboon_data = tomllib.load(f)
            print(GAB_VERSION_STRING.format(gaboon_data["project"]["version"]))
            return 0
    if len(argv) < 1 or argv[0].startswith("-"):
        docopt(__doc__, ["gab", "-h"])

    cmd = argv[0]
    # We look at the names of all the files in this folder, each file is a command
    cmd_list = [i.stem for i in Path(__file__).parent.glob("[!_]*.py")]
    if cmd not in cmd_list:
        distances = sorted(
            [(i, levenshtein_norm(cmd, i)) for i in cmd_list], key=lambda k: k[1]
        )
        if distances[0][1] <= 0.2:
            sys.exit(f"Invalid command. Did you mean 'brownie {distances[0][0]}'?")
        sys.exit("Invalid command. Try 'brownie --help' for available commands.")
    # We then call the `main` function of each command, and pass the args

    try:
        importlib.import_module(f"gaboon.cli.{cmd}").main()
    except Exception as e:
        sys.exit(f"Error running command '{cmd}': {e}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
