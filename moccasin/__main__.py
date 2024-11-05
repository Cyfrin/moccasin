import argparse
import sys
import tomllib
from importlib import import_module, metadata
from pathlib import Path
from typing import Tuple

from moccasin.constants.vars import CONFIG_NAME
from moccasin.logging import logger, set_log_level

MOCCASIN_CLI_VERSION_STRING = "Moccasin CLI v{}"

ALIAS_TO_COMMAND = {
    "build": "compile",
    "c": "compile",
    "script": "run",
    "config": "config_",
    "u": "utils",
    "util": "utils",
}

PRINT_HELP_ON_NO_SUB_COMMAND = ["run", "wallet", "explorer", "deployments"]


def main(argv: list) -> int:
    """Run the Moccasin CLI with the given arguments.

    Args:
        argv (list): List of arguments to run the CLI with.
    """
    if "--version" in argv or "version" in argv:
        print(get_version())
        return 0

    main_parser, sub_parsers = generate_main_parser_and_sub_parsers()

    # ------------------------------------------------------------------
    #                         PARSING STARTS
    # ------------------------------------------------------------------
    if len(argv) == 0 or (len(argv) == 1 and (argv[0] == "-h" or argv[0] == "--help")):
        main_parser.print_help()
        return 0

    if (
        ALIAS_TO_COMMAND.get(argv[0], argv[0]) in PRINT_HELP_ON_NO_SUB_COMMAND
        and len(argv) < 2
    ):
        parser_to_print = sub_parsers._name_parser_map[argv[0]]
        parser_to_print.print_help()
        return 0

    args = main_parser.parse_args(argv)
    set_log_level(quiet=args.quiet, debug=args.debug)

    if args.command:
        command_to_run = ALIAS_TO_COMMAND.get(args.command, args.command)
        logger.info(f"Running {command_to_run} command...")
        import_module(f"moccasin.commands.{command_to_run}").main(args)
    else:
        main_parser.print_help()
    return 0


def generate_main_parser_and_sub_parsers() -> (
    Tuple[argparse.ArgumentParser, argparse.Action]
):
    parent_parser = create_parent_parser()
    main_parser = argparse.ArgumentParser(
        prog="Moccasin CLI",
        description="🐍 Pythonic Smart Contract Development Framework",
        formatter_class=argparse.RawTextHelpFormatter,
        parents=[parent_parser],
    )
    sub_parsers = main_parser.add_subparsers(dest="command")

    # ------------------------------------------------------------------
    #                          INIT COMMAND
    # ------------------------------------------------------------------
    init_parser = sub_parsers.add_parser(
        "init",
        help="Initialize a new project.",
        description="""
This will create a basic directory structure at the path you specific, which looks like:
.
├── README.md
├── moccasin.toml
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
    init_parser.add_argument(
        "--vscode", help="Add a .vscode/settings.json file.", action="store_true"
    )
    init_parser.add_argument(
        "--pyproject", help="Add a pyproject.toml file.", action="store_true"
    )

    # ------------------------------------------------------------------
    #                        COMPILE COMMAND
    # ------------------------------------------------------------------
    compile_parser = sub_parsers.add_parser(
        "compile",
        help="Compiles the project.",
        description="""Compiles a specific Vyper contract or all vyper contracts in the project. \n
If no contract or contract path is given, this command will:
1. Find all .vy files in the src/ directory
2. Compile each file using the Vyper compiler
3. Output the compiled artifacts to the out/ directory

Use this command to prepare your contracts for deployment or testing.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        aliases=["build"],
        parents=[parent_parser],
    )

    compile_parser.add_argument(
        "contract_or_contract_path",
        nargs="?",
        help="Optional argument to compile a specific contract.",
    )

    zksync_ground = compile_parser.add_mutually_exclusive_group()
    zksync_ground.add_argument(
        "--network", help=f"Alias of the network (from the {CONFIG_NAME})."
    )

    zksync_ground.add_argument("--is_zksync", nargs="?", const=True, default=None)

    # ------------------------------------------------------------------
    #                          TEST COMMAND
    # ------------------------------------------------------------------
    test_parser = sub_parsers.add_parser(
        "test",
        help="Runs all tests in the project.",
        description="Runs pytest with boa context.",
        parents=[parent_parser],
    )
    test_parser.add_argument(
        "file_or_dir",
        help="Name of the test or folder to run tests on, or the path to your script.",
        type=str,
        nargs="?",
    )
    add_network_args_to_parser(test_parser)
    add_account_args_to_parser(test_parser)

    # Pytest args
    test_parser.add_argument(
        "--gas-profile",
        default=False,
        help="Get an output on gas use for test functions.",
        action="store_true",
    )
    test_parser.add_argument(
        "-k",
        nargs="?",
        help="""Only run tests which match the given substring expression. An expression is a Python evaluable expression where all names are
                        substring-matched against test names and their parent classes. Example: -k 'test_method or test_other' matches all test functions and
                        classes whose name contains 'test_method' or 'test_other', while -k 'not test_method' matches those that don't contain 'test_method' in
                        their names. -k 'not test_method and not test_other' will eliminate the matches. Additionally keywords are matched to classes and
                        functions containing extra names in their 'extra_keyword_matches' set, as well as functions which have names assigned directly to them.
                        The matching is case-insensitive.""",
    )
    test_parser.add_argument(
        "-m",
        nargs="?",
        help="""Only run tests matching given mark expression. For example: -m 'mark1 and not mark2'.""",
    )
    test_parser.add_argument(
        "-x",
        "--exitfirst",
        action="store_true",
        help="""Exit instantly on first error or failed test.""",
    )
    test_parser.add_argument(
        "-s",
        action="store_true",
        help="""A way to show print lines from tests. Shortcut for --capture=no""",
    )
    test_parser.add_argument(
        "--capture ",
        nargs="?",
        help="""Per-test capturing method: one of fd|sys|no|tee-sys""",
    )
    test_parser.add_argument(
        "--lf",
        "--last-failed",
        action="store_true",
        help="""Rerun only the tests that failed at the last run (or all if none failed).""",
    )
    test_parser.add_argument(
        "--cache-clear",
        action="store_true",
        help="""Remove all cache contents at start of test run.""",
    )
    test_parser.add_argument(
        "--disable-warnings",
        "--disable-pytest-warnings",
        action="store_true",
        help="""Disable warnings summary.""",
    )
    test_parser.add_argument(
        "--full-trace",
        action="store_true",
        help="Don't cut any tracebacks (default is to cut)",
    )
    test_parser.add_argument(
        "--pdb",
        action="store_true",
        help="Start the debugger for each test that fails.",
    )

    # Coverage Options
    test_parser.add_argument(
        "--coverage",
        action="store_true",
        help="Shorthand for adding `--cov=. --cov-branch`.",
    )
    test_parser.add_argument("--cov", help="Coverage target directory.", type=Path)
    test_parser.add_argument(
        "--cov-report",
        nargs="*",
        help="Type of report to generate: term, term-missing, annotate, html, xml, json, lcov (multi-allowed). term, term- missing may be followed by “:skip-covered”. annotate, html, xml, json and lcov may be followed by “:DEST” where DEST specifies the output location. Use –cov-report= to not generate any output..",
    )
    test_parser.add_argument(
        "--cov-config",
        help="Coverage config file, defaults to a moccasin internal config file loading the boa plugin.",
    )
    test_parser.add_argument(
        "--no-cov-on-fail",
        action="store_true",
        help="Do not report coverage if test run fails.",
    )
    test_parser.add_argument(
        "--no-cov", action="store_true", help="Disable coverage report."
    )
    test_parser.add_argument(
        "--cov-reset",
        action="store_true",
        help="Reset cov sources accumulated in options so far. Mostly useful for scripts and configuration files.",
    )
    test_parser.add_argument(
        "--cov-fail-under",
        type=int,
        help="Fail if the total coverage is less than this value.",
    )
    test_parser.add_argument(
        "--cov-append",
        action="store_true",
        help="Do not delete coverage but append to current. Default: False.",
    )
    test_parser.add_argument(
        "--cov-branch", action="store_true", help="Enable branch coverage."
    )
    test_parser.add_argument(
        "--cov-context", help="Coverage context to add to the coverage data."
    )
    test_parser.add_argument(
        "--tb",
        choices=["auto", "long", "short", "no", "line", "native"],
        help="Traceback print mode",
    )
    test_parser.add_argument(
        "-v", "--verbose", action="count", help="Verbosity level", default=None
    )

    # Hypothesis Options
    test_parser.add_argument(
        "--hypothesis-seed",
        type=int,
        help="Random seed to get the same run as a prior run.",
    )

    # Add pytest-xdist specific arguments
    test_parser.add_argument(
        "-n",
        "--numprocesses",
        help="Number of processes to use (auto/NUM)",
        default=None,
    )
    test_parser.add_argument(
        "--dist",
        choices=["load", "loadscope", "loadfile", "loadgroup", "no", "worksteal"],
        help="Load distribution mode",
        default=None,
    )

    # ------------------------------------------------------------------
    #                          RUN COMMAND
    # ------------------------------------------------------------------
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
    add_account_args_to_parser(run_parser)

    # ------------------------------------------------------------------
    #                         DEPLOY COMMAND
    # ------------------------------------------------------------------
    deploy_parser = sub_parsers.add_parser(
        "deploy",
        help="Deploys a contract named in the config with a deploy script.",
        description="Deploys a contract named in the config with a deploy script.",
        parents=[parent_parser],
    )
    deploy_parser.add_argument(
        "contract_name",
        help=f"Name of your named contract in your {CONFIG_NAME} to deploy.",
        type=str,
    )
    add_network_args_to_parser(deploy_parser)
    add_account_args_to_parser(deploy_parser)

    # ------------------------------------------------------------------
    #                         WALLET COMMAND
    # ------------------------------------------------------------------
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
        "--password-file", help="File containing the password for the keystore"
    )
    # Add custom validation
    generate_parser.set_defaults(func=validate_generate_args)

    # Import
    import_parser = wallet_subparsers.add_parser(
        "import",
        aliases=["i", "add"],
        help="Import a private key into an encrypted keystore",
    )
    import_parser.add_argument("name", help="Name of account to import")

    # Inspect Json
    view_parser = wallet_subparsers.add_parser(
        "view", help="View the JSON of a keystore file"
    )
    view_parser.add_argument("keystore_file_name", help="Name of keystore file")

    # Decrypt Keystore
    decrypt_keystore_parser = wallet_subparsers.add_parser(
        "decrypt", aliases=["dk"], help="Decrypt a keystore file to get the private key"
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
        "delete", aliases=["d"], help="Delete a keystore file"
    )
    delete_parser.add_argument("keystore_file_name", help="Name of keystore file")

    # ------------------------------------------------------------------
    #                        CONSOLE COMMAND
    # ------------------------------------------------------------------
    console_parser = sub_parsers.add_parser(
        "console",
        help="BETA, USE AT YOUR OWN RISK: Interact with the network in a python shell.",
        description="BETA, USE AT YOUR OWN RISK: Interact with the network in a python shell.\n",
        parents=[parent_parser],
    )
    add_network_args_to_parser(console_parser)
    add_account_args_to_parser(console_parser)

    # ------------------------------------------------------------------
    #                        INSTALL COMMAND
    # ------------------------------------------------------------------
    install_parser = sub_parsers.add_parser(
        "install",
        help="Installs the project's dependencies.",
        description="""Installs the project's dependencies. The first argument is the requirements, given as a pip-compatible strings and/or moccasin github formatted dependencies. 
- Pip-compatible strings download dependencies as regular python packages from PyPI.
- Moccasin github formatted dependencies download dependencies from the Moccasin github repository.

Moccasin github formatted dependencies are formatted as:

GITHUB_ORG/GITHUB_REPO@[@VERSION]

Where:
- GITHUB_ORG is the github organization or user that owns the repository.
- GITHUB_REPO is the name of the repository.
- VERSION is the optional version of the repository to download. If not provided, the latest version is downloaded.

Examples:
- pcaversaccio/snekmate@0.1.0 # Moccasin GitHub formatted dependency
- snekmate==0.1.0 # Pip-compatible string""",
        parents=[parent_parser],
    )
    install_parser.add_argument(
        "requirements",
        help="Requirements, given as a pip-compatible strings and/or moccasin github formatted dependencies.",
        type=str,
        nargs="*",
    )

    # ------------------------------------------------------------------
    #                         PURGE COMMAND
    # ------------------------------------------------------------------
    purge_parser = sub_parsers.add_parser(
        "purge",
        help="Purge a given dependency",
        description="Purge the given dependency.",
        parents=[parent_parser],
    )
    purge_parser.add_argument(
        "packages",
        help="Package name, given as a pip-compatible string and/or moccasin github formatted dependency.",
        type=str,
        nargs="+",
    )

    # ------------------------------------------------------------------
    #                         CONFIG COMMAND
    # ------------------------------------------------------------------
    sub_parsers.add_parser(
        "config",
        help="View the Moccasin configuration.",
        description="View the Moccasin configuration.",
        parents=[parent_parser],
    )

    # ------------------------------------------------------------------
    #                        EXPLORER COMMAND
    # ------------------------------------------------------------------
    explorer_parser = sub_parsers.add_parser(
        "explorer",
        help="Work with block explorers to get data.",
        description="Work with block explorers to get data.",
        parents=[parent_parser],
    )
    # Create subparsers under 'explorer'
    explorer_subparsers = explorer_parser.add_subparsers(dest="explorer_command")

    ## Explorer command: fetch
    get_parser = explorer_subparsers.add_parser(
        "fetch",
        aliases=["get"],
        help="Retrieve the ABI of a contract from a block explorer.",
        description="""Retreive the ABI of a contract from a block explorer.

This command will attempt to use the environment variable ETHERSCAN_API_KEY as the API key for Etherscan. If this environment variable is not set, you can provide the API key as an argument to the command.
""",
        parents=[parent_parser],
    )
    get_parser.add_argument(
        "address", help="The address you want to pull from.", type=str
    )
    get_parser.add_argument("--name", help="Optional name for the contract.", type=str)
    get_parser.add_argument(
        "--api-key",
        "--explorer-api-key",
        help="API key for the block explorer.",
        type=str,
    )
    get_parser.add_argument(
        "--ignore-config",
        "-i",
        help="Don't pull values from the config.",
        action="store_true",
    )
    get_parser.add_argument(
        "--save-abi-path",
        help="Location to save the returned abi. This will only be applied if you also add the '--save' flag.",
        type=str,
    )
    get_parser.add_argument(
        "--save",
        help="If added, the ABI will be saved to the 'save-abi-path' given in the command line or config.",
        action="store_true",
    )

    network_uri_or_chain = get_parser.add_mutually_exclusive_group()
    network_uri_or_chain.add_argument(
        "--explorer-uri", help="API URI endpoint for explorer.", type=str
    )
    network_uri_or_chain.add_argument(
        "--explorer-type", help="blockscout, etherscan, or zksyncexplorer.", type=str
    )
    network_uri_or_chain.add_argument(
        "--network",
        help=f"Name/alias of the network (from the {CONFIG_NAME}). If chain_id is set in the config, you may also use that.",
        type=str,
    )

    ## Explorer command: list
    explorer_list_parser = explorer_subparsers.add_parser(
        "list", help="List all natively supported block explorers and chains."
    )
    explorer_list_parser.add_argument(
        "--by-id", help="List by chain id.", action="store_true"
    )
    explorer_list_parser.add_argument(
        "--json", help="Format as json.", action="store_true"
    )

    # ------------------------------------------------------------------
    #                        INSPECT COMMAND
    # ------------------------------------------------------------------
    inspect_parser = sub_parsers.add_parser(
        "inspect",
        help="Inspect compiler data of a contract.",
        description="""Inspect compiler data of a contract. 
        
        This command will directly use the Vyper compiler to access this data. For example, to get function signatures and selectors run:
            
            mox inspect src/Counter.vy methods
            
        or
        
            mox inspect Counter methods""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    inspect_parser.add_argument(
        "contract",
        help="Path or Contract name of the contract you want to inspect.",
        type=str,
    )
    inspect_parser.add_argument(
        "inspect_type",
        help="Type of inspection you want to do.",
        choices=[
            "methods",
            "abi",
            "natspec",
            "storage-layout",
            "ir-nodes",
            "ir-runtime",
            "function-signatures",
            "function-selectors",
            "selectors",
            "signatures",
            "assembly",
            "venom-functions",
            "bytecode",
            "bytecode-runtime",
        ],
    )

    # ------------------------------------------------------------------
    #                      DEPLOYMENTS COMMAND
    # ------------------------------------------------------------------
    deployments_parser = sub_parsers.add_parser(
        "deployments",
        help="View deployments of the project from your DB.",
        description="""View deployments of the project from your DB.
        
        The --format-level will determine how much information you want to print based on your deployment.

        Format levels:
        - 0: Contract Address
        - 1: Contract Address and Name
        - 2: Contract Address, Name, and Source Code
        - 3: Everything
        - 4: Raw JSON
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[parent_parser],
    )
    deployments_parser.add_argument(
        "contract_name", help='Name of the contract to get, or "all".'
    )
    deployments_parser.add_argument(
        "--format-level",
        "-f",
        default=1,
        help="Format level of how much information you want to print based on your deployment.",
    )
    deployments_parser.add_argument(
        "--checked",
        action="store_true",
        help="Only return contracts that match the current edition of the code by comparing integrity hashes.",
    )
    deployments_parser.add_argument(
        "--limit", default=None, help="Limit the number of deployments to get."
    )
    add_network_args_to_parser(deployments_parser)

    # ------------------------------------------------------------------
    #                         UTILS COMMAND
    # ------------------------------------------------------------------
    utils_paraser = sub_parsers.add_parser(
        "utils",
        aliases=["u", "util"],
        help="Helpful utilities - right now it's just the one.",
        description="Helpful utilities.\n",
        parents=[parent_parser],
    )
    utils_subparaser = utils_paraser.add_subparsers(dest="utils_command")

    # Zero
    utils_subparaser.add_parser(
        "zero",
        aliases=["zero-address", "zero_address", "address-zero", "address_zero"],
        help="Get the zero address.",
    )

    # ------------------------------------------------------------------
    #                             RETURN
    # ------------------------------------------------------------------
    return main_parser, sub_parsers


# ------------------------------------------------------------------
#                        HELPER FUNCTIONS
# ------------------------------------------------------------------
def add_account_args_to_parser(parser: argparse.ArgumentParser):
    key_or_account_group = parser.add_mutually_exclusive_group()
    key_or_account_group.add_argument(
        "--account", help="Keystore account you want to use.", type=str
    )
    key_or_account_group.add_argument(
        "--private-key",
        help="Private key you want to use to get an unlocked account.",
        type=str,
    )

    password_group = parser.add_mutually_exclusive_group()
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


def add_network_args_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--fork",
        nargs="?",  # Allow an optional value
        const=True,  # Value when the flag is passed without an argument
        default=None,  # When no flag is passed, help="If you want to fork the RPC."
    )
    network_or_rpc_group = parser.add_mutually_exclusive_group()
    network_or_rpc_group.add_argument(
        "--network", help=f"Alias of the network (from the {CONFIG_NAME})."
    )
    network_or_rpc_group.add_argument(
        "--url", "--rpc", help="RPC URL to run the script on."
    )
    network_or_rpc_group.add_argument(
        "--prompt-live",
        nargs="?",  # Allow an optional value
        const=True,  # Value when the flag is passed without an argument
        default=None,  # When no flag is passed
        help="Prompt the user to make sure they want to run this script.",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="The location of your database, defaults to your working project's database in your {CONFIG_NAME}.",
    )
    parser.add_argument(
        "--save-to-db",
        nargs="?",  # Allow an optional value
        const=True,  # Value when the flag is passed without an argument
        default=None,  # When no flag is passed
        help="Save the deployment to the database.",
    )
    return parser


def get_version() -> str:
    version = metadata.version("moccasin")
    # Attempt to parse from `pyproject.toml` if not found
    if not version:
        with open(
            Path(__file__).resolve().parent.parent.joinpath("pyproject.toml"), "rb"
        ) as f:
            moccasin_cli_data = tomllib.load(f)
        version = moccasin_cli_data["project"]["version"]
    return MOCCASIN_CLI_VERSION_STRING.format(version)


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
