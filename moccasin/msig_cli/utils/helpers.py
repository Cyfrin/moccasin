import json
import os
from pathlib import Path
from typing import Optional, Tuple, cast

from eth_utils import to_bytes, to_checksum_address
from prompt_toolkit import HTML, print_formatted_text
from safe_eth.eth import EthereumClient
from safe_eth.safe import Safe, SafeTx
from safe_eth.util.util import to_0x_hex_str

from moccasin.msig_cli.constants import ERROR_INVALID_ADDRESS, ERROR_INVALID_RPC_URL
from moccasin.msig_cli.utils.types import (
    T_EIP712Domain,
    T_EIP712TxJson,
    T_SafeTxData,
    T_SafeTxMessage,
)
from moccasin.msig_cli.validators import is_valid_address, is_valid_rpc_url


def pretty_print_safe_tx(safe_tx: SafeTx):
    """Pretty-print SafeTx fields.

    :param safe_tx: SafeTx object to print.
    :type safe_tx: SafeTx
    """

    print_formatted_text(HTML("<b><orange>SafeTx</orange></b>"))
    print_formatted_text(HTML(f"\t<b><yellow>Nonce:</yellow></b> {safe_tx.safe_nonce}"))
    print_formatted_text(HTML(f"\t<b><yellow>To:</yellow></b> {safe_tx.to}"))
    print_formatted_text(HTML(f"\t<b><yellow>Value:</yellow></b> {safe_tx.value}"))
    print_formatted_text(
        HTML(f"\t<b><yellow>Data:</yellow></b> {to_0x_hex_str(safe_tx.data)}")
    )
    print_formatted_text(
        HTML(f"\t<b><yellow>Operation:</yellow></b> {safe_tx.operation}")
    )
    print_formatted_text(
        HTML(f"\t<b><yellow>SafeTxGas:</yellow></b> {safe_tx.safe_tx_gas}")
    )
    print_formatted_text(HTML(f"\t<b><yellow>BaseGas:</yellow></b> {safe_tx.base_gas}"))
    print_formatted_text(
        HTML(f"\t<b><yellow>GasPrice:</yellow></b> {safe_tx.gas_price}")
    )
    print_formatted_text(
        HTML(f"\t<b><yellow>GasToken:</yellow></b> {safe_tx.gas_token}")
    )
    print_formatted_text(
        HTML(f"\t<b><yellow>RefundReceiver:</yellow></b> {safe_tx.refund_receiver}")
    )
    print_formatted_text(HTML(f"\t<b><yellow>Signers:</yellow></b> {safe_tx.signers}"))


def parse_eth_type_value(val, typ):
    """Parse a value according to its Ethereum type.

    :param val: The value to parse.
    :param typ: The Ethereum type of the value (e.g., "uint256", "address", "bool", etc.).
    """
    # @TODO: Handle more complex types like arrays, structs, etc.
    if typ.startswith("uint") or typ.startswith("int"):
        return int(val)
    if typ == "address":
        return val if val.startswith("0x") else "0x" + val
    if typ == "bool":
        return val.lower() in ("true", "1", "yes")
    if typ.startswith("bytes"):
        return to_bytes(hexstr=val)
    return val


def get_signatures_bytes(signatures: Optional[str]) -> bytes:
    """Get signatures bytes from JSON value or return empty bytes.

    :param signatures: Signatures in hex format or None.
    :type signatures: Optional[str]

    :return: Signatures as bytes.
    """
    if signatures:
        # Use JSON value if present
        hex_str = signatures.lstrip("0x") if signatures.startswith("0x") else signatures
        return bytes.fromhex(hex_str)
    else:
        # Default to empty bytes
        return b""


def get_custom_eip712_structured_data(safe_tx: SafeTx) -> dict:
    """Get the EIP-712 structured data from a SafeTx.

    :param safe_tx: SafeTx object to extract the structured data from.

    :return: A dictionary containing the EIP-712 structured data.
    """
    # Get the EIP-712 structured data and wrap it in a dictionary with signatures
    eip712_struct = safe_tx.eip712_structured_data
    eip712_struct["message"]["data"] = to_0x_hex_str(eip712_struct["message"]["data"])
    # Convert signatures to hex format
    safe_tx_data = {
        "safeTx": eip712_struct,
        "signatures": to_0x_hex_str(safe_tx.signatures),
    }

    return safe_tx_data


def get_multisend_address_from_env(var_name="TEST_MULTISEND_ADDRESS"):
    """Get the MultiSend contract address from environment variables.

    :param var_name: The name of the environment variable to check for the MultiSend address.
    :return: The MultiSend contract address as a checksummed address, or None if not set.
    """
    address = os.environ.get(var_name)
    return to_checksum_address(address) if address else None


def get_safe_instance(ethereum_client: EthereumClient, safe_address: str) -> Safe:
    """Initialize the Safe instance with the provided RPC URL and Safe address.

    :param rpc_url: The RPC URL to connect to the Ethereum network.
    :param safe_address: The address of the Safe contract.
    :return: An instance of the Safe class.
    :raises ValueError: If the address or RPC URL is invalid.
    """
    assert is_valid_address(safe_address), ERROR_INVALID_ADDRESS
    assert is_valid_rpc_url(ethereum_client.ethereum_node_url), ERROR_INVALID_RPC_URL
    safe_address_checksum = to_checksum_address(safe_address)
    return Safe(address=safe_address_checksum, ethereum_client=ethereum_client)  # type: ignore[abstract]


def extract_safe_tx_json(
    safe_tx_json: T_SafeTxData | T_EIP712TxJson,
) -> Tuple[Optional[T_EIP712Domain], Optional[T_SafeTxMessage], Optional[str]]:
    """
    Validate SafeTx JSON input, extract message, domain, and signatures, and strictly enforce domain matching.

    :param safe_tx_json: The loaded JSON dict from file.
    :param safe_instance: The Safe instance to match against (if available).

    :return: (message_json, domain_json, signatures_json)
    """
    # Extract message, domain, signatures from SafeTx JSON or EIP-712 JSON
    message_json = None
    domain_json = None
    signatures_json = None
    if "safeTx" in safe_tx_json:
        safe_tx_eip712 = safe_tx_json["safeTx"]  # type: ignore
        message_json = cast(T_SafeTxMessage, safe_tx_eip712.get("message"))
        domain_json = cast(T_EIP712Domain, safe_tx_eip712.get("domain"))
        signatures_val = safe_tx_json.get("signatures")
        signatures_json = (
            cast(Optional[str], signatures_val)
            if signatures_val is None or isinstance(signatures_val, str)
            else str(signatures_val)
        )
    elif all(k in safe_tx_json for k in ("types", "domain", "message")):
        message_json = cast(T_SafeTxMessage, safe_tx_json.get("message"))
        domain_json = cast(T_EIP712Domain, safe_tx_json.get("domain"))
    else:
        return None, None, None

    # Enforce domain and message are present
    if domain_json is None or message_json is None:
        return None, None, None

    return domain_json, message_json, signatures_json


def validate_ethereum_client_chain_id(
    ethereum_client: EthereumClient, domain_json: T_EIP712Domain
) -> None:
    """Validate the chainId in the domain JSON against the Ethereum client.

    :param ethereum_client: The Ethereum client instance.
    :param domain_json: The domain JSON containing the chainId.

    :raises MsigCliError: If the chainId does not match the Ethereum client's chainId.
    """
    if "chainId" not in domain_json:
        raise Exception("Domain JSON must contain 'chainId' field.")

    eth_chain_id = ethereum_client.get_chain_id()
    if domain_json["chainId"] != eth_chain_id:
        raise Exception(
            f"Domain chainId {domain_json['chainId']} does not match Ethereum client chainId {eth_chain_id}."
        )


def build_safe_tx_from_message(
    safe_instance: Safe, message_json: T_SafeTxMessage, signatures_json: bytes
) -> SafeTx:
    """Build a SafeTx from the provided message JSON and optional signatures.

    :param safe_instance: The Safe instance to use for building the transaction.
    :param message_json: The message JSON containing the transaction details.
    :param signatures_json: Optional signatures in hex format.

    :return: A SafeTx object initialized with the provided message and signatures.
    :raises MsigCliError: If there is an error creating the SafeTx.
    """
    try:
        # Convert the message to SafeTx
        return safe_instance.build_multisig_tx(
            to=to_checksum_address(message_json["to"]),
            value=message_json["value"],
            data=bytes.fromhex(
                message_json["data"].lstrip("0x")
                if message_json["data"].startswith("0x")
                else message_json["data"]
            ),
            operation=message_json["operation"],
            safe_nonce=message_json["nonce"],
            safe_tx_gas=message_json["safeTxGas"],
            base_gas=message_json["baseGas"],
            gas_price=message_json["gasPrice"],
            gas_token=to_checksum_address(message_json["gasToken"]),
            refund_receiver=to_checksum_address(message_json["refundReceiver"]),
            signatures=signatures_json,
        )
    except Exception as e:
        raise Exception(f"Error creating SafeTx from message JSON: {e}") from e


def save_safe_tx_json(output_json: Path, safe_tx_data: dict) -> None:
    """Save the SafeTx data as JSON to the specified output file."""
    with open(output_json, "w") as f:
        json.dump(safe_tx_data, f, indent=2, default=str)
    print_formatted_text(
        HTML(f"<b><green>Saved EIP-712 JSON:</green> {output_json}</b>")
    )


def check_funds_account(
    safe_tx_gas: int, base_gas: int, gas_price: int, gas_token: str
) -> bool:
    """
    Check account has enough funds to pay for a SafeTx

    :param safe_tx_gas: Safe tx gas
    :param base_gas: Data gas
    :param gas_price: Gas Price
    :param gas_token: Gas Token, to use token instead of ether for the gas
    :return: `True` if enough funds, `False` otherwise
    """
    if gas_token == NULL_ADDRESS:
        balance = self.ethereum_client.get_balance(self.address)
    else:
        balance = self.ethereum_client.erc20.get_balance(self.address, gas_token)
    return balance >= (safe_tx_gas + base_gas) * gas_price
