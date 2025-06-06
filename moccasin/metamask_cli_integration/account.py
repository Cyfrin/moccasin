import json
from queue import Empty
from typing import Dict

from boa.util.abi import Address

from moccasin.logging import logger
from moccasin.metamask_cli_integration.constants import (
    TRANSACTION_CONFIRMATION_TIMEOUT_S,
)
from moccasin.metamask_cli_integration.server_control import get_server_control


class MetaMaskAccount:
    """A custom account class that delegates transaction sending
    and broadcasting to the MetaMask UI.

    This account does NOT hold a private key. It implements the interface
    (address property, send_transaction method) expected by Boa's external provider flow.

    :param address: The MetaMask account address as a string.
    :type address: str

    :ivar _address_boa: The account address as a boa.util.abi.Address object.
    :vartype _address_boa: Address
    """

    def __init__(self, address: str):
        self._address_boa = Address(address)

    @property
    def address(self) -> Address:  # Returns boa.util.abi.Address
        """Returns the account address as boa.util.abi.Address."""
        return self._address_boa

    def send_transaction(self, raw_tx_data: dict) -> Dict[str, str]:
        """Delegates transaction sending to the MetaMask UI.

        This method is called by Boa when `account` does not have `sign_transaction`.

        :param raw_tx_data: The raw transaction data to send, as a dictionary.
        :type raw_tx_data: dict
        :return: A dictionary containing the transaction hash if successful.
        :rtype: Dict[str, str]
        :raises RuntimeError: If the MetaMask UI server is not running.
        :raises TimeoutError: If the user does not confirm the transaction in time.
        :raises Exception: If the MetaMask UI transaction fails with an error.
        """
        control = get_server_control()
        if not control.server_thread or not control.server_thread.is_alive():
            raise RuntimeError(
                "MetaMask UI server is not running. Cannot send transaction via UI."
            )

        logger.info(
            f"Delegating transaction to MetaMask UI for address {self.address}..."
        )
        try:
            # Send raw_tx_data to the browser for signing/broadcasting
            control.transaction_request_queue.put(raw_tx_data)

            # Wait for the browser to send back the result (hash or error)
            # Use a long timeout as user interaction can take time
            # Assuming network sync happened already, this wait is for transaction confirmation.
            result_json = control.transaction_response_queue.get(
                timeout=TRANSACTION_CONFIRMATION_TIMEOUT_S
            )
            result = json.loads(result_json)

            if result.get("status") == "success":
                tx_hash = result["hash"]
                logger.info(
                    f"Transaction confirmed and broadcasted by MetaMask. Hash: {tx_hash}"
                )
                # Boa expects a dictionary with a 'hash' key from this method
                return {"hash": tx_hash}
            else:
                error_message = result.get("error", "Unknown MetaMask UI error")
                error_code = result.get("code", "N/A")
                raise Exception(
                    f"MetaMask transaction failed: {error_message} (Code: {error_code})"
                )
        except Empty:
            raise TimeoutError(
                "Timed out waiting for MetaMask transaction response from UI. User did not confirm in time."
            )
        except Exception as e:
            logger.error(f"Error during MetaMask UI transaction delegation: {e}")
            raise  # Re-raise the exception to propagate failure

    def __repr__(self):
        return f"<MetaMaskAccount {self.address}>"
