import importlib
from pathlib import Path
import tomllib
import argparse
from gaboon.logging import logger, set_log_level
import sys
from gaboon.constants import CONFIG_NAME


GAB_CLI_VERSION_STRING= "Gaboon CLI v{}"

def main(argv: list) -> int:
    if "--version" in argv or "version" in argv:
        print(get_version())
    
    main_parser = argparse.ArgumentParser(
        prog="Gaboon CLI",
        description="🐍 Pythonic Smart Contract Development Framework",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    main_parser.add_argument(
        "-d", "--debug", action="store_true", help="Run in debug mode"
    )
    main_parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress all output except errors"
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
    # TODO

    # Test command
    # ========================================================================
    # TODO

     # Run command
    # ========================================================================
    run_parser = sub_parsers.add_parser(
        "run",
        help="Runs a script with the project's context.",
        description="Runs a script with the project's context.",
    )
    run_parser.add_argument(
        "script_name_or_path",
        help="Name of the script in the script folder, or the path to your script.",
        type=str,
        default="./script/deploy.py",
    )

    network_or_rpc_group = run_parser.add_mutually_exclusive_group()
    network_or_rpc_group.add_argument("--network", help=f"Alias of the network (from the {CONFIG_NAME}).")
    network_or_rpc_group.add_argument("--rpc", help="RPC URL to run the script on.")

    key_or_account_group = run_parser.add_mutually_exclusive_group()
    key_or_account_group.add_argument("--account", help="Keystore account you want to use.", type=str)
    key_or_account_group.add_argument(
        "--private-key",
        help="Private key you want to use to get an unlocked account.",
        type=str,
    )
    # TODO pass in password or password file

    # Wallet command
    # ========================================================================
    wallet_parser = sub_parsers.add_parser(
        "wallet",
        help="Wallet management utilities.",
        description="Wallet management utilities.\n",
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

    # Private Key
    private_key_parser = wallet_subparsers.add_parser(
        "private-key", aliases=["pk"], help="Derives private key from mnemonic"
    )
    private_key_parser.add_argument("mnemonic", help="Mnemonic phrase")

    # Decrypt Keystore
    decrypt_keystore_parser = wallet_subparsers.add_parser(
        "decrypt-keystore",
        aliases=["dk"],
        help="Decrypt a keystore file to get the private key",
    )
    decrypt_keystore_parser.add_argument(
        "keystore_file", help="Path to the keystore file"
    )
    decrypt_keystore_parser.add_argument("password", help="Password to decrypt")

    # Delete
    decrypt_keystore_parser = wallet_subparsers.add_parser(
        "delete",
        aliases=["d"],
        help="Delete a keystore file",
    )
    decrypt_keystore_parser.add_argument(
        "keystore_file_name", help="Name of keystore file"
    )

    ######################
    ### PARSING STARTS ###
    ######################
    if len(argv) == 0 or (len(argv) == 1 and (argv[0] == "-h" or argv[0] == "--help")):
        main_parser.print_help()
        return 0
    args = main_parser.parse_args(argv)
    set_log_level(quiet=args.quiet, debug=args.debug)
    logger.info(f"Running {args.command} command...")
    if args.command:
        importlib.import_module(f"gaboon.commands.{args.command}").main(args)
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

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
