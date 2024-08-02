import importlib
from pathlib import Path
import tomllib
import argparse
from gaboon.logging import logger, set_log_level
import sys
from gaboon.constants.vars import CONFIG_NAME


GAB_CLI_VERSION_STRING = "Gaboon CLI v{}"

ALIAS_TO_COMMAND = {
    "build": "compile",
    "c": "compile",
    "script": "run",
}

PRINT_HELP_ON_NO_SUB_COMMAND = ["run", "wallet"]


def main(argv: list) -> int:
    if "--version" in argv or "version" in argv:
        print(get_version())

    parent_parser = create_parent_parser()

    main_parser = argparse.ArgumentParser(
        prog="Gaboon CLI",
        description="🐍 Pythonic Smart Contract Development Framework",
        formatter_class=argparse.RawTextHelpFormatter,
        parents=[parent_parser],
    )
    sub_parsers = main_parser.add_subparsers(dest="command")

    # Init command
    # ========================================================================
    init_parser = sub_parsers.add_parser(
        "init",
        help="Initialize a new project.",
        description="""
This will create a basic directory structure at the path you specific, which looks like:
.
├── README.md
├── titanoboa.toml
├── script
│   └── deploy.py
├── src
│   └── Counter.vy
└── tests
    ├── conftest.py
    └── test_counter.py
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[parent_parser],
    )
    init_parser.add_argument(
        "path",
        help="Path of the new project, defaults to current directory.",
        type=Path,
        nargs="?",
        default=Path("."),
    )
    init_parser.add_argument(
        "-f",
        "--force",
        required=False,
        help="Overwrite existing project.",
        action="store_true",
    )

    # Compile command
    # ========================================================================
    sub_parsers.add_parser(
        "compile",
        help="Compiles the project.",
        description="""Compiles all Vyper contracts in the project. \n
This command will:
1. Find all .vy files in the src/ directory
2. Compile each file using the Vyper compiler
3. Output the compiled artifacts to the out/ directory

Use this command to prepare your contracts for deployment or testing.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        aliases=["build"],
        parents=[parent_parser],
    )

    # Test command
    # ========================================================================
    test_parser = sub_parsers.add_parser(
        "test",
        help="Runs all tests in the project.",
        description="Runs pytest with boa context.",
        parents=[parent_parser],
    )
    add_network_args_to_parser(test_parser)
    test_parser.add_argument(
        "pytest_args", nargs="*", help="Arguments to be passed to pytest."
    )

    # Run command
    # ========================================================================
    run_parser = sub_parsers.add_parser(
        "run",
        help="Runs a script with the project's context.",
        description="Runs a script with the project's context.",
        aliases=["script"],
        parents=[parent_parser],
    )
    run_parser.add_argument(
        "script_name_or_path",
        help="Name of the script in the script folder, or the path to your script.",
        type=str,
        default="./script/deploy.py",
    )
    add_network_args_to_parser(run_parser)

    key_or_account_group = run_parser.add_mutually_exclusive_group()
    key_or_account_group.add_argument(
        "--account", help="Keystore account you want to use.", type=str
    )
    key_or_account_group.add_argument(
        "--private-key",
        help="Private key you want to use to get an unlocked account.",
        type=str,
    )

    password_group = run_parser.add_mutually_exclusive_group()
    password_group.add_argument(
        "--password",
        help="Password for the keystore account.",
        action=RequirePasswordAction,
    )
    password_group.add_argument(
        "--password-file-path",
        help="Path to the file containing the password for the keystore account.",
        action=RequirePasswordAction,
    )

    # Wallet command
    # ========================================================================
    wallet_parser = sub_parsers.add_parser(
        "wallet",
        help="Wallet management utilities.",
        description="Wallet management utilities.\n",
        parents=[parent_parser],
    )
    wallet_subparsers = wallet_parser.add_subparsers(dest="wallet_command")

    # List
    wallet_subparsers.add_parser(
        "list",
        aliases=["ls"],
        help="List all the accounts in the keystore default directory",
    )

    # Generate
    generate_parser = wallet_subparsers.add_parser(
        "generate",
        aliases=["g", "new"],
        help="Create a new account with a random private key",
    )
    generate_parser.add_argument("name", help="Name of account")
    generate_parser.add_argument("--save", help="Save to keystore", action="store_true")
    # Create a group for password options
    password_group = generate_parser.add_mutually_exclusive_group()
    password_group.add_argument("--password", help="Password for the keystore")
    password_group.add_argument(
        "--password-file",
        help="File containing the password for the keystore",
    )
    # Add custom validation
    generate_parser.set_defaults(func=validate_generate_args)

    # Import
    import_parser = wallet_subparsers.add_parser(
        "import", aliases=["i"], help="Import a private key into an encrypted keystore"
    )
    import_parser.add_argument("name", help="Name of account to import")

    # Inspect Json
    inspect_parser = wallet_subparsers.add_parser(
        "inspect", help="View the JSON of a keystore file"
    )
    inspect_parser.add_argument("keystore_file_name", help="Name of keystore file")

    # Decrypt Keystore
    decrypt_keystore_parser = wallet_subparsers.add_parser(
        "decrypt",
        aliases=["dk"],
        help="Decrypt a keystore file to get the private key",
    )
    decrypt_keystore_parser.add_argument(
        "keystore_file_name", help="Name of the keystore file to decrypt"
    )
    decrypt_password_group = decrypt_keystore_parser.add_mutually_exclusive_group()
    decrypt_password_group.add_argument(
        "--password",
        help="Password for the keystore account.",
        action=RequirePasswordAction,
    )
    decrypt_password_group.add_argument(
        "--password-file-path",
        help="Path to the file containing the password for the keystore account.",
        action=RequirePasswordAction,
    )
    decrypt_keystore_parser.add_argument(
        "--print-key",
        "-p",
        action="store_true",
        help="Print the private key to the console",
    )

    # Delete
    delete_parser = wallet_subparsers.add_parser(
        "delete",
        aliases=["d"],
        help="Delete a keystore file",
    )
    delete_parser.add_argument("keystore_file_name", help="Name of keystore file")

    ######################
    ### PARSING STARTS ###
    ######################
    if len(argv) == 0 or (len(argv) == 1 and (argv[0] == "-h" or argv[0] == "--help")):
        main_parser.print_help()
        return 0

    # Test fix
    # Since we want to be able to pass any flags into pytest, we need to separate the flags before parsing
    pytest_args = []
    if len(argv) > 1 and argv[0] == "test" and argv[1] != "--help" and argv[1] != "-h":
        pytest_args = argv[1:]
        argv = argv[:1]

    if argv[0] in PRINT_HELP_ON_NO_SUB_COMMAND and len(argv) < 2:
        parser_to_print = sub_parsers._name_parser_map[argv[0]]
        parser_to_print.print_help()
        return 0

    args = main_parser.parse_args(argv)
    set_log_level(quiet=args.quiet, debug=args.debug)

    if args.command:
        command_to_run = ALIAS_TO_COMMAND.get(args.command, args.command)
        logger.info(f"Running {command_to_run} command...")
        # TODO - fix this so we can do forking tests
        if command_to_run == "test":
            args = pytest_args
        importlib.import_module(f"gaboon.commands.{command_to_run}").main(args)
    else:
        main_parser.print_help()
    return 0


######################
## Helper Functions ##
######################
def find_project_root(start_path: Path | str = Path.cwd()) -> Path:
    current_path = Path(start_path).resolve()
    while True:
        if (current_path / CONFIG_NAME).exists():
            return current_path

        # Check for src directory with .vy files in current directory
        src_path = current_path / "src"
        if src_path.is_dir() and any(src_path.glob("*.vy")):
            return current_path

        # Check for titanoboa.toml in parent directory
        if (current_path.parent / CONFIG_NAME).exists():
            return current_path.parent

        # Move up to the parent directory
        parent_path = current_path.parent
        if parent_path == current_path:
            # We've reached the root directory without finding titanoboa
            raise FileNotFoundError(
                f"Could not find {CONFIG_NAME} or src directory with Vyper contracts in any parent directory"
            )
        current_path = parent_path


def add_network_args_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--fork", action="store_true", help="If you want to fork the RPC."
    )
    network_or_rpc_group = parser.add_mutually_exclusive_group()
    network_or_rpc_group.add_argument(
        "--network", help=f"Alias of the network (from the {CONFIG_NAME})."
    )
    network_or_rpc_group.add_argument(
        "--url", "--rpc", help="RPC URL to run the script on."
    )
    return network_or_rpc_group


def get_version() -> int:
    with open(
        Path(__file__).resolve().parent.parent.joinpath("pyproject.toml"), "rb"
    ) as f:
        boa_cli_data = tomllib.load(f)
        return GAB_CLI_VERSION_STRING.format(boa_cli_data["project"]["version"])


def validate_generate_args(args):
    if args.save and not (args.password or args.password_file):
        raise argparse.ArgumentTypeError(
            "When using --save, you must provide either --password or --password-file"
        )


def create_parent_parser():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-d", "--debug", action="store_true", help="Run in debug mode")
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress all output except errors"
    )
    return parser


class RequirePasswordAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not hasattr(namespace, "account") or namespace.account is None:
            parser.error(f"{option_string} can only be used with --account")
        setattr(namespace, self.dest, values)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
