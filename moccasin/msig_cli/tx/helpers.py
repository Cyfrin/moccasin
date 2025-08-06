from typing import Optional
from eth_utils import to_bytes
from prompt_toolkit import HTML, print_formatted_text
from safe_eth.safe import SafeTx
from safe_eth.util.util import to_0x_hex_str


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


def get_signatures(
    cli_signatures: Optional[str], json_signatures: Optional[str]
) -> bytes:
    """Get signatures from CLI input or JSON value.

    If CLI signatures are provided, they take precedence.
    If JSON signatures are provided, they are used if CLI signatures are not.
    If neither is provided, return empty bytes.

    :param cli_signatures: Signatures from CLI input in hex format.
    :param json_signatures: Signatures from JSON value in hex format.

    :return: Signatures as bytes.
    """
    if cli_signatures:
        # Always use CLI input if provided
        return bytes.fromhex(cli_signatures)
    elif json_signatures:
        # Use JSON value if present
        return bytes.fromhex(json_signatures)
    else:
        # Default to empty bytes
        return b""
