import http.server
import json
import time
from queue import Empty

from moccasin.logging import logger
from moccasin.metamask_cli_integration.server_control import Address, get_server_control


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

    def log_request(self, code="-", size="-"):
        """
        Overrides the default log_request to suppress verbose HTTP access logs.
        """
        pass  # Do nothing to suppress the logging

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

        # Check account status endpoint
        elif self.path == "/check_account_status":
            # Return the current account status
            account_status = getattr(control, "account_status", {"ok": True})
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(account_status).encode("utf-8"))
            logger.debug(f"Sent account status: {account_status}")

        # Endpoint for checking disconnect signal
        elif self.path == "/api/check_disconnect_signal":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response_data = {"disconnect": control.signal_disconnect_frontend}
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
            # Reset the signal after sending it, so it's not repeatedly sent
            control.signal_disconnect_frontend = False

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
            # Call the base class method to serve the file
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

        # Handle account connection status reports (including rejections)
        elif self.path == "/report_account_connection_status":
            try:
                data = json.loads(post_body)
                account = data.get("account")
                status = data.get("status")

                if status == "connected":
                    if account:
                        control.connected_account_address = Address(account)
                        control.connected_account_event.set()
                        control.user_declined_account_connection = False
                        logger.info(f"Received connected MetaMask account: {account}")
                        self.send_response(200)
                        self.send_header("Content-type", "text/plain")
                        self.end_headers()
                        self.wfile.write(b"Account connected.")
                    else:
                        logger.warning(
                            "Received 'connected' status but no account address."
                        )
                        self.send_response(400)
                        self.end_headers()
                elif status == "rejected":
                    control.connected_account_address = None  # Ensure it's clear
                    # Set the event here even on rejection to unblock the main thread!
                    control.connected_account_event.set()
                    control.user_declined_account_connection = True  # Set the new flag
                    logger.info("MetaMask account connection rejected by user.")
                    self.send_response(200)  # Still a successful receipt of status
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(
                        b"Account connection rejected. Server will shut down."
                    )  # Inform browser
                elif status == "error" or status == "disconnected":
                    control.connected_account_address = None
                    control.connected_account_event.clear()
                    control.user_declined_account_connection = False
                    logger.warning(
                        f"MetaMask account connection status: {status}. Account: {account}"
                    )
                    self.send_response(200)
                    self.end_headers()
                else:
                    logger.warning(
                        f"Unknown account connection status received: {status}"
                    )
                    self.send_response(400)
                    self.end_headers()

            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON in request body.")
            except Exception as e:
                logger.error(f"Error handling /report_account_connection_status: {e}")
                self.send_error(500, "Internal server error.")

        # API endpoint for network synchronization signal
        # This is where the browser signals that the MetaMask network is synced
        elif self.path == "/api/network-synced":
            control.network_sync_event.set()
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")

        # Handle browser closing signal
        # This endpoint is called when the browser tab is closed or the user disconnects
        # It allows the server to clean up resources or set flags for graceful shutdown
        elif self.path == "/browser_closing":
            try:
                data = json.loads(post_body)
                account = data.get("account")
                action = data.get("action")
                if account and action == "disconnect":
                    logger.info(
                        f"Browser closing signal received for account: {account}. "
                        "Attempting to clear connected account in backend."
                    )
                    # Clear the connected account and associated events,
                    # as the frontend is indicating a disconnect.
                    control.connected_account_address = None
                    control.connected_account_event.clear()
                    # You might also want to interrupt any ongoing waiting processes
                    # or set a flag that the browser session is terminated.
                    self.send_response(200)
                    self.end_headers()
                else:
                    self.send_error(400, "Invalid payload for browser_closing.")
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON in request body.")
            except Exception as e:
                logger.error(f"Error handling /browser_closing: {e}")
                self.send_error(500, "Internal server error.")

        else:
            # Default behavior
            super().do_POST()
