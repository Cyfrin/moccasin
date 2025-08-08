import argparse

from moccasin.msig_cli.validators import (
    validate_address,
    validate_data,
    validate_json_file,
    validate_number,
    validate_rpc_url,
    validate_signer,
)


def _add_common_args(parser: argparse.ArgumentParser):
    """Add common arguments to the parser that are shared across multiple commands."""
    parser.add_argument(
        "--rpc-url",
        help="RPC URL to connect to the Ethereum network.",
        type=validate_rpc_url,
    )


def _add_tx_builder_args(parser: argparse.ArgumentParser):
    """Add transaction builder arguments to the parser."""
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
        help="Output file to save the SafeTx structured data as JSON.",
        type=validate_json_file,
    )


def _add_tx_signer_args(parser: argparse.ArgumentParser):
    """Add transaction signer arguments to the parser."""
    parser.add_argument(
        "--signer",
        help="Signer account name from mox wallet or private key to use for signing the transaction. Private key is discouraged for security reasons, only use for testing purposes.",
        type=validate_signer,
    )
    parser.add_argument(
        "--input-json",
        help="Path to a JSON file containing the SafeTx data to sign.",
        type=validate_json_file,
    )
    parser.add_argument(
        "--output-json",
        help="Output file to save the signed SafeTx data as JSON.",
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
    # Add the tx_build command
    tx_build_parser = msig_subparsers.add_parser(
        "tx_build", help="Build a multisig transaction."
    )
    _add_common_args(tx_build_parser)
    _add_tx_builder_args(tx_build_parser)

    # Add the tx_sign command
    tx_sign_parser = msig_subparsers.add_parser(
        "tx_sign", help="Sign a multisig transaction."
    )
    _add_common_args(tx_sign_parser)
    _add_tx_signer_args(tx_sign_parser)

    # Store references for help display
    msig_parser._subparsers = msig_subparsers
    msig_parser._tx_build_parser = tx_build_parser
    msig_parser._tx_sign_parser = tx_sign_parser

    return msig_parser
