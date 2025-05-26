import http.server
import importlib.resources
import json
import socketserver
import threading
import webbrowser
import time

from pathlib import Path
from queue import Queue, Empty
from typing import Optional, Dict

from boa.util.abi import Address
from eth_utils.address import to_checksum_address

from moccasin.logging import logger

# --- Global Variables for Server Communication ---
HEARTBEAT_INTERVAL_CLIENT_MS = 5000  # JS client heartbeat interval
HEARTBEAT_TIMEOUT_SERVER_S = 15  # Python server timeout for client heartbeat


# --- Server Control Object ---
class MetamaskServerControl:
    """Manages the state and communication for the MetaMask UI server."""

    def __init__(self, port: int):
        self.port = port
        self.shutdown_flag = threading.Event()
        self.network_sync_event = (
            threading.Event()
        )  # NEW: Signals when network is synced
        self.transaction_request_queue = Queue()  # CLI -> Browser
        self.transaction_response_queue = Queue()  # Browser -> CLI
        self.connected_account_event = (
            threading.Event()
        )  # Signals when account is connected
        self.connected_account_address: Optional[Address] = None
        self.last_heartbeat_time = time.time()
        self.httpd: Optional[socketserver.TCPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.browser_thread: Optional[threading.Thread] = None
        self.heartbeat_timeout_s = HEARTBEAT_TIMEOUT_SERVER_S


# Global instance of server control, managed by _setup_network_and_account_from_config_and_cli
_server_control: Optional[MetamaskServerControl] = None


def set_server_control(control: MetamaskServerControl):
    """Sets the global server control instance."""
    global _server_control
    _server_control = control


def get_server_control() -> MetamaskServerControl:
    """Gets the global server control instance."""
    if _server_control is None:
        raise RuntimeError(
            "MetaMask server control not initialized. Call start_metamask_ui_server first."
        )
    return _server_control


# --- MetaMask Account Class (for boa.env.eoa) ---
class MetaMaskAccount:
    """
    A custom account class that delegates transaction sending
    and broadcasting to the MetaMask UI. This account does NOT hold a private key.
    It implements the interface (address property, send_transaction method)
    expected by Boa's external provider flow.
    """

    def __init__(self, address: str):
        self._address_boa = Address(address)
        self._address_checksum_str = to_checksum_address(address)

        logger.info(
            f"MetaMaskAccount initialized with address: {self._address_checksum_str}"
        )

    @property
    def address(self) -> Address:  # Returns boa.util.abi.Address
        """Returns the account address as boa.util.abi.Address."""
        return self._address_boa

    def send_transaction(self, raw_tx_data: dict) -> Dict[str, str]:
        """
        Delegates transaction sending to the MetaMask UI.
        This method is called by Boa when `account` does not have `sign_transaction`.
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

    def __repr__(self):
        return f"<MetaMaskAccount {self.address}>"


# --- Server Handler ---
class CustomHandler(http.server.SimpleHTTPRequestHandler):
    """
    A custom HTTP request handler for the MetaMask integration server.
    It serves static files and handles API endpoints for transaction details,
    shutdown, heartbeat, and dynamic transaction requests, and now network sync.
    """

    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=str(directory), **kwargs)

    def do_GET(self):
        control = get_server_control()
        if self.path == "/get_pending_transaction":
            try:
                tx_params = control.transaction_request_queue.get_nowait()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(tx_params).encode("utf-8"))
                logger.debug("Sent transaction parameters to browser.")
            except Empty:
                self.send_response(204)
                self.end_headers()
                logger.debug("No pending transaction request for browser.")

        elif self.path == "/heartbeat":
            control.last_heartbeat_time = time.time()
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")

        elif self.path == "/api/boa-network-details":
            chain_id = "unknown"
            rpc_url = "unknown"
            network_name = "Boa Local Network"

            # Assuming boa.env is globally accessible after Boa setup
            try:
                # Import boa.env here to ensure it's initialized
                from boa import env as boa_env

                # Attempt to get chain_id from boa.env directly
                if hasattr(boa_env, "chain_id") and boa_env.chain_id is not None:
                    chain_id = boa_env.chain_id
                else:  # Fallback to fetching if chain_id is not a direct property or is None
                    # This might raise RPCError if the RPC is not responsive or EIP-1559/legacy fees can't be fetched
                    _base_fee, _priority_fee, _max_fee, chain_id_hex = (
                        boa_env.get_eip1559_fee()
                    )
                    chain_id = int(chain_id_hex, 16)  # Convert hex string to integer

                # Safely get rpc_url, assuming it's an attribute of the active network
                rpc_url = getattr(boa_env, "rpc_url", "unknown")

                # Try to make a more specific name if possible
                if hasattr(boa_env, "nickname") and boa_env.nickname not in [
                    None,
                    "unknown",
                    "",
                ]:
                    network_name = boa_env.nickname.capitalize() + " Network"
                elif chain_id == 31337:  # Common Anvil default
                    network_name = "Anvil Localhost"
                else:
                    network_name = (
                        f"Boa Network (ID: {chain_id})"  # Fallback using Chain ID
                    )

            except (ImportError, AttributeError, Exception) as e:
                logger.warning(
                    f"Could not reliably determine boa_env Chain ID/RPC for UI: {e}"
                )
                # Keep defaults if detection fails

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "chainId": str(chain_id),  # Send as string for JS
                        "rpcUrl": rpc_url,
                        "networkName": network_name,
                    }
                ).encode("utf-8")
            )
        else:
            super().do_GET()

    def do_POST(self):
        control = get_server_control()
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            post_body = self.rfile.read(content_length).decode("utf-8")
        else:
            post_body = "{}"

        if self.path == "/report_transaction_result":
            control.transaction_response_queue.put(post_body)
            logger.info(f"Received transaction result from browser: {post_body}")
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Result received.")

        elif self.path == "/report_connected_account":
            data = json.loads(post_body)
            connected_address = data.get("account")
            if connected_address:
                control.connected_account_address = Address(connected_address)
                control.connected_account_event.set()
                logger.info(f"Received connected MetaMask account: {connected_address}")
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Account received.")
            else:
                logger.warning("No account address received from browser.")
                self.send_response(400)
                self.end_headers()

        # NEW API ENDPOINT FOR NETWORK SYNC SIGNAL
        elif self.path == "/api/network-synced":
            control.network_sync_event.set()  # Signal that network is synced
            logger.info("Received signal from UI: MetaMask network is synchronized.")
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            super().do_POST()


# --- Server Utilities ---
def _open_browser_tab(port: int):
    control = get_server_control()
    try:
        # Open the specific HTML file that handles network sync first
        webbrowser.open(f"http://localhost:{port}/index.html")
    except Exception as e:
        logger.error(f"Failed to open browser tab: {e}")
        control.shutdown_flag.set()


def _heartbeat_monitor(control: MetamaskServerControl):
    while not control.shutdown_flag.is_set():
        if time.time() - control.last_heartbeat_time > control.heartbeat_timeout_s:
            logger.warning(
                f"\nNo heartbeat received for {control.heartbeat_timeout_s} seconds. Assuming browser closed. Shutting down server..."
            )
            control.shutdown_flag.set()  # Signal main thread to shut down server
            break
        time.sleep(1)


def _run_http_server(port: int, ui_files_path: Path, control: MetamaskServerControl):
    class Handler(CustomHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=ui_files_path, **kwargs)

    try:

        class ReusableTCPServer(socketserver.TCPServer):
            allow_reuse_address = True

        httpd = ReusableTCPServer(("", port), Handler)
        control.httpd = httpd
        logger.debug(f"MetaMask UI server started at http://localhost:{port}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"MetaMask UI server error: {e}")
    finally:
        logger.debug("MetaMask UI server stopped.")
        control.shutdown_flag.set()


# --- CLI Orchestration Functions ---
def start_metamask_ui_server() -> MetamaskServerControl:
    PORT = 9000
    control = MetamaskServerControl(PORT)
    set_server_control(control)

    try:
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

    control.server_thread = threading.Thread(
        target=_run_http_server, args=(PORT, ui_files_path, control)
    )
    control.server_thread.daemon = True
    control.server_thread.start()

    time.sleep(0.5)

    control.monitor_thread = threading.Thread(
        target=_heartbeat_monitor, args=(control,)
    )
    control.monitor_thread.daemon = True

    # Open browser immediately to start network sync process
    control.browser_thread = threading.Thread(target=_open_browser_tab, args=(PORT,))
    control.browser_thread.daemon = True
    control.browser_thread.start()

    logger.info(
        "MetaMask UI launched. Please check the browser window for network synchronization."
    )
    logger.info(f"If the tab didn't open, visit http://localhost:{PORT}/index.html")

    # --- NEW: Wait for network sync first ---
    logger.info("Waiting for MetaMask network synchronization...")
    if not control.network_sync_event.wait(
        timeout=control.heartbeat_timeout_s * 5  # Longer timeout for initial sync
    ):
        logger.error(
            "Timed out waiting for MetaMask network synchronization. Please ensure MetaMask is connected and the page is open."
        )
        stop_metamask_ui_server(control)
        raise TimeoutError("MetaMask network synchronization timed out.")

    # --- Then wait for account connection (if not already received during sync) ---
    # This part should be called *after* network sync, as account connection might depend on it.
    if (
        not control.connected_account_address
    ):  # Only wait if address not already set by JS sync
        logger.info("MetaMask network synced. Waiting for account connection...")
        if not control.connected_account_event.wait(
            timeout=control.heartbeat_timeout_s * 2
        ):
            logger.error(
                "Timed out waiting for MetaMask account connection. Ensure account is connected."
            )
            stop_metamask_ui_server(control)
            raise TimeoutError(
                "MetaMask account connection timed out after network sync."
            )

    if not control.connected_account_address:
        stop_metamask_ui_server(control)
        raise RuntimeError("MetaMask account connection failed. No address received.")

    logger.info(f"MetaMask account connected: {control.connected_account_address}")
    return control


def stop_metamask_ui_server(control: MetamaskServerControl):
    """Gracefully stops the MetaMask UI server."""
    if control and control.httpd:
        control.shutdown_flag.set()
        control.httpd.shutdown()
        control.httpd.server_close()
        logger.debug("MetaMask UI server gracefully stopped and closed.")
    else:
        logger.debug("MetaMask UI server not running or already stopped.")
