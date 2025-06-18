import json
from queue import Empty
from typing import Dict

from eth_typing import ChecksumAddress, HexAddress
from eth_utils.address import to_checksum_address

from moccasin.logging import logger
from moccasin.metamask_cli_integration.constants import (
    TRANSACTION_CONFIRMATION_TIMEOUT_S,
)
from moccasin.metamask_cli_integration.server_control import get_server_control
from moccasin.metamask_cli_integration.utils import convert_json_serializable_types


class MetaMaskAccount:
    """A custom account class that delegates transaction sending
    and broadcasting to the MetaMask UI.

    This account does NOT hold a private key. It implements the interface
    (address property, send_transaction method) expected by Boa's external provider flow.

    :param address: The MetaMask account address as a string.
    :type address: str

    :ivar _address_boa: The account address as a ChecksumAddress object.
    :vartype _address_boa: ChecksumAddress
    """

    def __init__(self, address: str | HexAddress):
        # Store as ChecksumAddress type
        if isinstance(address, str):
            self._address_boa = to_checksum_address(address)
        else:
            self._address_boa = ChecksumAddress(address)

    @property
    def address(self) -> ChecksumAddress:
        """Returns the account address as ChecksumAddress."""
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

    def sign_typed_data(self, full_message: dict) -> str:
        """Signs EIP-712 typed data using MetaMask.

        This method delegates typed data signing to the MetaMask UI. It's designed to work
        with a Python dictionary representing the EIP-712 typed data structure.

        @dev see https://github.com/vyperlang/titanoboa-zksync/blob/803d41456045ab54d0af44d929f95e9106c7bd14/boa_zksync/types.py#L105

        :param full_message: A Python dictionary containing the EIP-712 structured data.
                             This dict MUST conform to the EIP-712 specification,
                             including 'types', 'primaryType', 'domain', and 'message' fields.
                             All byte values within this dict must already be converted
                             to '0x'-prefixed hexadecimal strings.
        :type full_message: dict
        :return: The signature as a hex string.
        :rtype: str
        :raises RuntimeError: If the MetaMask UI server is not running.
        :raises TimeoutError: If the user does not sign the message in time.
        :raises Exception: If the MetaMask UI message signing fails with an error.
        """
        control = get_server_control()
        if not control.server_thread or not control.server_thread.is_alive():
            raise RuntimeError(
                "MetaMask UI server is not running. Cannot sign typed data via UI."
            )

        logger.info(
            f"Delegating typed data signing to MetaMask UI for address {self.address}..."
        )
        try:
            # Apply the recursive conversion here, BEFORE it's put into message_request
            # @dev This will convert all HexBytes and bytes objects within your full_message
            #     into 0x-prefixed hex strings, making the entire dictionary JSON serializable.
            processed_typed_data_payload = convert_json_serializable_types(
                full_message  # Changed from typed_data_payload to full_message
            )
            message_request = {
                "type": "eth_signTypedData_v4",  # Use the full RPC method name
                "payload": processed_typed_data_payload,
                "account": str(self.address),
            }

            # Send message signing request to the browser
            control.message_signing_request_queue.put(message_request)

            # Wait for the browser to send back the signature
            result_json = control.message_signing_response_queue.get(
                timeout=control.heartbeat_timeout_s * 10
            )
            result = json.loads(result_json)

            if result.get("status") == "success":
                signature = result["signature"]
                # Log the first 10 characters of the signature for brevity
                logger.info(
                    f"Typed data signed successfully by MetaMask. Signature: {signature[:10]}..."
                )
                return signature
            else:
                error_message = result.get("error", "Unknown MetaMask UI error")
                error_code = result.get("code", "N/A")
                raise Exception(
                    f"MetaMask typed data signing failed: {error_message} (Code: {error_code})"
                )
        except Empty:
            raise TimeoutError(
                "Timed out waiting for MetaMask typed data signing response from UI. User did not sign in time."
            )
        except Exception as e:
            logger.error(f"Error during MetaMask UI typed data signing delegation: {e}")
            raise  # Re-raise the exception to propagate failure

    def __repr__(self):
        return f"<MetaMaskAccount {self.address}>"
