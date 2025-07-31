from enum import Enum
from prompt_toolkit import HTML, print_formatted_text
from safe_eth.util.util import to_0x_hex_str
from safe_eth.safe import SafeTx


################################################################
#                            ENUMS                             #
################################################################
class TransactionType(Enum):
    CONTRACT_CALL = 0
    ERC20_TRANSFER = 1
    RAW = 2


################################################################
#                          EXCEPTIONS                          #
################################################################
# Exception to signal returning to prompt loop
class GoBackToPrompt(Exception):
    pass


################################################################
#                           HELPERS                            #
################################################################
def pretty_print_safe_tx(safe_tx: SafeTx):
    """Pretty-print SafeTx fields."""

    print_formatted_text(HTML("<b>SafeTx</b>"))
    print_formatted_text(
        HTML(f"<b>Nonce:</b> {safe_tx.nonce}"),
        HTML(f"<b>To:</b> {to_0x_hex_str(safe_tx.to)}"),
        HTML(f"<b>Value:</b> {safe_tx.value}"),
        HTML(f"<b>Data:</b> {to_0x_hex_str(safe_tx.data)}"),
        HTML(f"<b>Operation:</b> {safe_tx.operation}"),
        HTML(f"<b>SafeTxGas:</b> {safe_tx.safe_tx_gas}"),
        HTML(f"<b>BaseGas:</b> {safe_tx.base_gas}"),
        HTML(f"<b>GasPrice:</b> {safe_tx.gas_price}"),
        HTML(f"<b>GasToken:</b> {to_0x_hex_str(safe_tx.gas_token)}"),
        HTML(f"<b>RefundReceiver:</b> {to_0x_hex_str(safe_tx.refund_receiver)}"),
        HTML(
            f"<b>Signers:</b> {', '.join([to_0x_hex_str(addr) for addr in safe_tx.signers])}"
        ),
    )
