# Metamask integration for Moccasin CLI
# This module provides a server to interact with MetaMask for transaction signing
# and account management, allowing users to delegate transaction handling
# to the MetaMask UI instead of using private keys directly in the CLI.

import http.server
import importlib.resources
import json
import socketserver
import threading
import time
import webbrowser
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Dict, Optional

from boa.util.abi import Address

from moccasin.logging import logger

################################################################
#          GLOBAL VARIABLES FOR SERVER COMMUNICATION           #
################################################################
HEARTBEAT_INTERVAL_CLIENT_MS = 5000  # JS client heartbeat interval
HEARTBEAT_TIMEOUT_SERVER_S = 15  # Python server timeout for client heartbeat


################################################################
#                    SERVER CONTROL OBJECT                     #
################################################################
class MetamaskServerControl:
    """Manages the state and communication for the MetaMask UI server.

    This class holds the server state, queues for transaction requests and responses,
    and synchronization events for network and account management.
    It is used to control the server lifecycle, handle transactions, and manage
    the connection with the MetaMask UI.

    :param port: The port on which the MetaMask UI server will run.
    :type port: int

    :ivar port: The port number for the server.
    :vartype port: int
    :ivar shutdown_flag: Event to signal server shutdown.
    :vartype shutdown_flag: threading.Event
    :ivar network_sync_event: Event to signal that the network is synced.
    :vartype network_sync_event: threading.Event
    :ivar transaction_request_queue: Queue for transaction requests from CLI to browser.
    :vartype transaction_request_queue: Queue
    :ivar transaction_response_queue: Queue for transaction responses from browser to CLI.
    :vartype transaction_response_queue: Queue
    :ivar connected_account_event: Event to signal that a MetaMask account is connected.
    :vartype connected_account_event: threading.Event
    :ivar connected_account_address: The address of the connected MetaMask account.
    :vartype connected_account_address: Optional[Address]
    :ivar last_heartbeat_time: Timestamp of the last heartbeat received from the browser.
    :vartype last_heartbeat_time: float
    :ivar httpd: The HTTP server instance.
    :vartype httpd: Optional[socketserver.TCPServer]
    :ivar server_thread: Thread running the HTTP server.
    :vartype server_thread: Optional[threading.Thread]
    :ivar monitor_thread: Thread monitoring the server heartbeat.
    :vartype monitor_thread: Optional[threading.Thread]
    :ivar browser_thread: Thread for opening the browser tab.
    :vartype browser_thread: Optional[threading.Thread]
    :ivar heartbeat_timeout_s: Timeout for heartbeat checks in seconds.
    :vartype heartbeat_timeout_s: int
    :ivar boa_network_details: Details about the network to use for the MetaMask UI.
    :vartype boa_network_details: Dict[str, Any]
    """

    def __init__(self, port: int):
        self.port = port
        self.shutdown_flag = threading.Event()
        self.network_sync_event = threading.Event()
        self.transaction_request_queue: Queue[dict] = Queue()  # CLI -> Browser
        self.transaction_response_queue: Queue[str] = Queue()  # Browser -> CLI
        self.message_signing_request_queue: Queue[dict] = Queue()  # CLI -> Browser for message signing
        self.message_signing_response_queue: Queue[str] = Queue()  # Browser -> CLI for message signing
        self.connected_account_event = threading.Event()
        self.connected_account_address: Optional[Address] = None
        self.last_heartbeat_time = time.time()
        self.httpd: Optional[socketserver.TCPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.browser_thread: Optional[threading.Thread] = None
        self.heartbeat_timeout_s = HEARTBEAT_TIMEOUT_SERVER_S
        self.boa_network_details: Dict[str, Any] = {}
        self.account_status: Dict[str, Any] = {"ok": False}


# Global instance of server control, managed by _setup_network_and_account_from_config_and_cli
_server_control: Optional[MetamaskServerControl] = None


def set_server_control(control: MetamaskServerControl):
    """Sets the global server control instance.

    :param control: The MetamaskServerControl instance to set.
    :type control: MetamaskServerControl
    """
    global _server_control
    _server_control = control


def get_server_control() -> MetamaskServerControl:
    """Gets the global server control instance.

    :return: The current MetamaskServerControl instance.
    :rtype: MetamaskServerControl
    :raises RuntimeError: If the server control has not been initialized.
    """
    if _server_control is None:
        raise RuntimeError(
            "MetaMask server control not initialized. Call start_metamask_ui_server first."
        )
    return _server_control


################################################################
#                    METAMASK ACCOUNT CLASS                    #
################################################################
# @dev for Boa's EOA, we need a custom account class
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
                timeout=control.heartbeat_timeout_s
                * 10  # Extended timeout for user interaction
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

    def sign_message(self, encoded_message):
        """Signs an encoded message using MetaMask.

        This method delegates message signing to the MetaMask UI. It's designed to work
        with the encoded output from encode_typed_data() which is used in ZkSync deployments.

        :param encoded_message: The encoded message to sign (bytes from encode_typed_data)
        :type encoded_message: bytes
        :return: The signature as a hex string.
        :rtype: str
        :raises RuntimeError: If the MetaMask UI server is not running.
        :raises TimeoutError: If the user does not sign the message in time.
        :raises Exception: If the MetaMask UI message signing fails with an error.
        """
        control = get_server_control()
        if not control.server_thread or not control.server_thread.is_alive():
            raise RuntimeError(
                "MetaMask UI server is not running. Cannot sign message via UI."
            )

        # Convert bytes to hex string for transmission to browser
        if isinstance(encoded_message, bytes):
            message_hex = "0x" + encoded_message.hex()
        else:
            # Handle case where it's already a string
            message_hex = str(encoded_message)
            if not message_hex.startswith("0x"):
                message_hex = "0x" + message_hex

        logger.info(
            f"Delegating message signing to MetaMask UI for address {self.address}..."
        )
        try:
            # Prepare message signing request
            message_request = {
                "type": "sign_message",
                "message": message_hex,
                "account": str(self.address)
            }
            
            # Send message signing request to the browser
            control.message_signing_request_queue.put(message_request)

            # Wait for the browser to send back the signature
            result_json = control.message_signing_response_queue.get(
                timeout=control.heartbeat_timeout_s * 10  # Extended timeout for user interaction
            )
            result = json.loads(result_json)

            if result.get("status") == "success":
                signature = result["signature"]
                logger.info(
                    f"Message signed successfully by MetaMask. Signature: {signature[:10]}..."
                )
                return signature
            else:
                error_message = result.get("error", "Unknown MetaMask UI error")
                error_code = result.get("code", "N/A")
                raise Exception(
                    f"MetaMask message signing failed: {error_message} (Code: {error_code})"
                )
        except Empty:
            raise TimeoutError(
                "Timed out waiting for MetaMask message signing response from UI. User did not sign in time."
            )
        except Exception as e:
            logger.error(f"Error during MetaMask UI message signing delegation: {e}")
            raise  # Re-raise the exception to propagate failure

    def __repr__(self):
        return f"<MetaMaskAccount {self.address}>"


################################################################
#                        SERVER HANDLER                        #
################################################################
class CustomHandler(http.server.SimpleHTTPRequestHandler):
    """A custom HTTP request handler for the MetaMask integration server.

    It serves static files and handles API endpoints for transaction details,
    shutdown, heartbeat, and dynamic transaction requests, and now network sync.

    :param args: Positional arguments for the base class.
    :param directory: The directory to serve files from.
    :type directory: str or Path
    :param kwargs: Keyword arguments for the base class.
    :type kwargs: dict
    """

    def __init__(self, *args, directory=None, **kwargs):
        # Initialize the base class with the specified directory
        # @dev Base class is SimpleHTTPRequestHandler, which serves files from the directory
        super().__init__(*args, directory=str(directory), **kwargs)

    def do_GET(self):
        """Handles GET requests for the MetaMask UI server.

        It serves static files and handles specific API endpoints for
        transaction requests, heartbeat checks, and network details.
        """
        control = get_server_control()
        # Get the pending transaction request from the queue
        if self.path == "/get_pending_transaction":
            try:
                # Attempt to get the transaction parameters from the queue
                tx_params = control.transaction_request_queue.get_nowait()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                # Convert the transaction parameters to JSON and send them
                self.wfile.write(json.dumps(tx_params).encode("utf-8"))
                logger.debug("Sent transaction parameters to browser.")
            except Empty:
                # If no transaction request is pending, respond with 204 No Content
                self.send_response(204)
                self.end_headers()
                logger.debug("No pending transaction request for browser.")
        # Heartbeat endpoint to keep the server alive
        elif self.path == "/heartbeat":
            # Update the last heartbeat time to keep the server alive
            control.last_heartbeat_time = time.time()
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        # Network details endpoint for MetaMask UI
        elif self.path == "/api/boa-network-details":
            # Use the network details stored in the MetaMask server control
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(control.boa_network_details).encode("utf-8"))
        elif self.path == "/check_account_status":
            # Return the current account status
            account_status = getattr(control, "account_status", {"ok": True})
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(account_status).encode("utf-8"))
            logger.debug(f"Sent account status: {account_status}")
        # Get pending message signing request from the queue
        elif self.path == "/get_pending_message_signing":
            try:
                # Attempt to get the message signing request from the queue
                message_request = control.message_signing_request_queue.get_nowait()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                # Convert the message signing request to JSON and send it
                self.wfile.write(json.dumps(message_request).encode("utf-8"))
                logger.debug("Sent message signing request to browser.")
            except Empty:
                # If no message signing request is pending, respond with 204 No Content
                self.send_response(204)
                self.end_headers()
                logger.debug("No pending message signing request for browser.")
        else:
            # @dev maybe not needed, but just in case?
            super().do_GET()

    def do_POST(self):
        """Handles POST requests for the MetaMask UI server.

        It processes transaction results from the browser, connected account information,
        and network synchronization signals.
        It updates the server control state based on the received data.
        """
        control = get_server_control()
        content_length = int(self.headers.get("Content-Length", 0))
        # Read the POST body data
        if content_length > 0:
            post_body = self.rfile.read(content_length).decode("utf-8")
        else:
            post_body = "{}"

        # API endpoint for reporting transaction results
        # This is where the browser sends back the transaction result after user confirmation
        if self.path == "/report_transaction_result":
            control.transaction_response_queue.put(post_body)
            logger.info(f"Received transaction result from browser: {post_body}")
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Result received.")

        # API endpoint for reporting message signing results
        # This is where the browser sends back the message signature after user confirmation
        elif self.path == "/report_message_signing_result":
            control.message_signing_response_queue.put(post_body)
            logger.info(f"Received message signing result from browser: {post_body}")
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Message signing result received.")

        # API endpoint for reporting connected MetaMask account
        # This is where the browser sends back the connected account address
        elif self.path == "/report_connected_account":
            data = json.loads(post_body)
            connected_address = data.get("account")
            if connected_address:
                # Update the MetaMask server control with the connected account address
                control.connected_account_address = Address(connected_address)
                control.connected_account_event.set()

                # Notify the server that the account is connected
                logger.info(f"Received connected MetaMask account: {connected_address}")
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Account received.")
            else:
                # If no account address is provided, log a warning and respond with an error
                logger.warning("No account address received from browser.")
                self.send_response(400)
                self.end_headers()

        # API endpoint for network synchronization signal
        # This is where the browser signals that the MetaMask network is synced
        elif self.path == "/api/network-synced":
            control.network_sync_event.set()
            # Signal that network is synced
            logger.info("Received signal from UI: MetaMask network is synchronized.")
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            # Default behavior
            # @dev maybe not needed, but just in case?
            super().do_POST()


################################################################
#                       SERVER UTILITIES                       #
################################################################
def _open_browser_tab(port: int):
    """Opens a new browser tab to the MetaMask UI server.

    This function is called in a separate thread to avoid blocking the server startup.
    It attempts to open our custom MetaMask UI page for network synchronization.

    :param port: The port on which the MetaMask UI server is running.
    :type port: int
    """
    control = get_server_control()
    try:
        # Open the specific HTML file that handles network sync first
        webbrowser.open(f"http://localhost:{port}/index.html")
    except Exception as e:
        logger.error(f"Failed to open browser tab: {e}")
        control.shutdown_flag.set()


def _heartbeat_monitor(control: MetamaskServerControl):
    """Monitors the heartbeat from the browser to ensure it is still active.

    This function runs in a separate thread and checks if the last heartbeat
    was received within the specified timeout period.
    If the heartbeat timeout is exceeded, it signals the server to shut down.
    This is crucial for detecting if the browser tab was closed or if the connection was lost.

    :param control: The MetamaskServerControl instance managing the server state.
    :type control: MetamaskServerControl
    """
    while not control.shutdown_flag.is_set():
        if time.time() - control.last_heartbeat_time > control.heartbeat_timeout_s:
            logger.warning(
                f"\nNo heartbeat received for {control.heartbeat_timeout_s} seconds. Assuming browser closed. Shutting down server..."
            )
            control.shutdown_flag.set()  # Signal main thread to shut down server
            break
        time.sleep(1)


def _run_http_server(port: int, ui_files_path: Path, control: MetamaskServerControl):
    """Runs the HTTP server to serve the MetaMask UI files and handle API requests.

    This function is executed in a separate thread to allow the main thread to remain responsive.
    It sets up the server to listen on the specified port and serves files from the provided directory.

    :param port: The port on which the server will run.
    :type port: int
    :param ui_files_path: The path to the directory containing the MetaMask UI files.
    :type ui_files_path: Path
    :param control: The MetamaskServerControl instance managing the server state.
    :type control: MetamaskServerControl
    """

    class Handler(CustomHandler):
        """Custom request handler for serving MetaMask UI files and handling API requests."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=ui_files_path, **kwargs)

    try:

        class ReusableTCPServer(socketserver.TCPServer):
            """A TCP server that allows address reuse to avoid port conflicts."""

            allow_reuse_address = True

        # Create the HTTP server with the custom handler
        httpd = ReusableTCPServer(("", port), Handler)
        control.httpd = httpd
        logger.debug(f"MetaMask UI server started at http://localhost:{port}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"MetaMask UI server error: {e}")
    finally:
        # Ensure the server is properly closed on shutdown
        logger.debug("MetaMask UI server stopped.")
        control.shutdown_flag.set()


################################################################
#                 CLI ORCHESTRATION FUNCTIONS                  #
################################################################
def start_metamask_ui_server(
    boa_network_details: Dict[str, Any],
) -> MetamaskServerControl:
    """Starts the MetaMask UI server and prepares it for network synchronization.

    This function initializes the server control, sets up the HTTP server,
    and opens the MetaMask UI in a web browser for user interaction.
    It waits for the MetaMask network to sync and the user to connect their account.

    :param boa_network_details: Details about the network to use for the MetaMask UI.
    :type boa_network_details: Dict[str, Any]
    :return: The MetamaskServerControl instance managing the server state.
    :rtype: MetamaskServerControl
    :raises FileNotFoundError: If the MetaMask UI files cannot be located.
    :raises RuntimeError: If the server control has not been initialized.
    :raises TimeoutError: If the MetaMask network synchronization or account connection times out.
    """
    # Initialize the server MetaMask server control
    PORT = 9000
    control = MetamaskServerControl(PORT)
    set_server_control(control)

    # Store the network details in the MetaMask server control for the handler to access
    control.boa_network_details = boa_network_details

    try:
        # Attempt to locate the MetaMask UI files within the package resources
        with importlib.resources.path("moccasin.data", "metamask_ui") as p:
            ui_files_path = p
        if not ui_files_path.is_dir():
            raise FileNotFoundError(f"MetaMask UI directory not found: {ui_files_path}")
    except Exception as e:
        logger.error(f"Could not locate MetaMask UI files within package: {e}")
        logger.error(
            "Please ensure 'moccasin/data/metamask_ui/' is properly installed with your package."
        )
        raise

    logger.debug(f"Serving MetaMask UI from: {ui_files_path}")

    # Start the HTTP server in a separate thread
    # This allows the server to run concurrently with the main thread.
    control.server_thread = threading.Thread(
        target=_run_http_server, args=(PORT, ui_files_path, control)
    )
    control.server_thread.daemon = (
        True  # @dev daemon thread will exit when the main program exits
    )
    control.server_thread.start()

    # Wait a moment to ensure the server is ready before opening the browser
    time.sleep(0.5)

    # Start the heartbeat monitor thread to check for browser activity
    control.monitor_thread = threading.Thread(
        target=_heartbeat_monitor, args=(control,)
    )
    control.monitor_thread.daemon = True

    # Open browser to start network sync process
    control.browser_thread = threading.Thread(target=_open_browser_tab, args=(PORT,))
    control.browser_thread.daemon = True
    control.browser_thread.start()

    logger.info(
        "MetaMask UI launched. Please check the browser window for network synchronization."
    )
    logger.info(f"If the tab didn't open, visit http://localhost:{PORT}/index.html")

    # Wait for the browser to signal that the MetaMask network is synced
    logger.info("Waiting for MetaMask network synchronization...")
    if not control.network_sync_event.wait(
        timeout=control.heartbeat_timeout_s * 5  # Longer timeout for initial sync
    ):
        # If the network sync event is not set within the timeout, log an error and stop the server
        logger.error(
            "Timed out waiting for MetaMask network synchronization. Please ensure MetaMask is connected and the page is open."
        )
        stop_metamask_ui_server(control)
        raise TimeoutError("MetaMask network synchronization timed out.")

    # Then wait for MetaMask account connection (if not already received during sync)
    # This part should be called *after* network sync, as account connection might depend on it.
    if (
        not control.connected_account_address
    ):  # Only wait if address not already set by JS sync
        logger.info("MetaMask network synced. Waiting for account connection...")
        if not control.connected_account_event.wait(
            timeout=control.heartbeat_timeout_s * 2
        ):
            # If the account connection event is not set within the timeout, log an error and stop the server
            logger.error(
                "Timed out waiting for MetaMask account connection. Ensure account is connected."
            )
            stop_metamask_ui_server(control)
            raise TimeoutError(
                "MetaMask account connection timed out after network sync."
            )

    # If we reach here, the account should be connected
    # @dev in case the JS didn't send the account address, we raise an error
    if not control.connected_account_address:
        stop_metamask_ui_server(control)
        raise RuntimeError("MetaMask account connection failed. No address received.")

    # If everything is successful, return the MetaMask server control
    logger.info(f"MetaMask account connected: {control.connected_account_address}")
    return control


def stop_metamask_ui_server(control: MetamaskServerControl):
    """Gracefully stops the MetaMask UI server.

    This function signals the server to shut down, closes the HTTP server,
    and cleans up any resources used by the server control.

    :param control: The MetamaskServerControl instance managing the server state.
    :type control: MetamaskServerControl
    """
    if control and control.httpd:
        control.shutdown_flag.set()
        control.httpd.shutdown()
        control.httpd.server_close()
        logger.debug("MetaMask UI server gracefully stopped and closed.")
    else:
        logger.debug("MetaMask UI server not running or already stopped.")
