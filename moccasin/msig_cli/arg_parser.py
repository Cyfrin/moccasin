import argparse
from moccasin.msig_cli.validators import (
    validate_address,
    validate_rpc_url,
    validate_number,
    validate_data,
    validate_json_file,
)


def _add_tx_builder_args(parser: argparse.ArgumentParser):
    """Add transaction builder arguments to the parser."""
    parser.add_argument(
        "--rpc-url",
        help="RPC URL to connect to the Ethereum network.",
        type=validate_rpc_url,
    )
    parser.add_argument(
        "--safe-address",
        help="Address of the Safe contract to interact with.",
        type=validate_address,
    )
    parser.add_argument(
        "--to", help="Address of the contract to call.", type=validate_address
    )
    parser.add_argument(
        "--operation",
        help="Operation type: 0 for call, 1 for delegate call.",
        type=validate_number,
    )
    parser.add_argument(
        "--value",
        help="Value to send with the transaction, in wei.",
        type=validate_number,
    )
    parser.add_argument(
        "--data",
        help="Data to send with the transaction, in hex format.",
        type=validate_data,
    )
    parser.add_argument(
        "--safe-nonce",
        help="Nonce of the Safe contract to use for the transaction.",
        type=validate_number,
    )
    parser.add_argument(
        "--gas-token",
        help="Token to use for gas, defaults to the native token of the network.",
        type=validate_address,
    )
    parser.add_argument(
        "--json-output",
        help="Output file to save the EIP-712 structured data as JSON.",
        type=validate_json_file,
    )


def create_msig_parser():
    """Create and return the msig command line argument parser."""
    # Create the main parser for msig commands
    # @dev add_help is set to False to avoid conflicts with subcommands
    msig_parser = argparse.ArgumentParser(
        "mox msig", formatter_class=argparse.RawTextHelpFormatter, add_help=False
    )
    msig_subparsers = msig_parser.add_subparsers(dest="msig_command")

    # ----- Transaction subcommands -----
    tx_builder_parser = msig_subparsers.add_parser(
        "tx_build", help="Build a multisig transaction."
    )
    _add_tx_builder_args(tx_builder_parser)

    # ----- Message subcommands -----
    # @TODO Implement sign command
    # msg_parser = msig_subparsers.add_parser(
    #     "msg", help="Sign a transaction or message."
    # )
    # @TODO Add sign args here

    # Store references for help display
    msig_parser._subparsers = msig_subparsers
    msig_parser._tx_builder_parser = tx_builder_parser
    # msig_parser._msg_parser = msg_parser

    return msig_parser
