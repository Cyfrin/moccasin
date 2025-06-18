import socketserver
import time
import webbrowser
from pathlib import Path

from eth_utils import encode_hex
from hexbytes import HexBytes

from moccasin.logging import logger
from moccasin.metamask_cli_integration.http_handler import CustomHandler
from moccasin.metamask_cli_integration.server_control import (
    MetamaskServerControl,
    get_server_control,
)


def open_browser_tab(port: int):
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
        # Update heartbeat time as soon as browser is instructed to open
        control.last_heartbeat_time = time.time()
    except Exception as e:
        logger.error(f"Failed to open browser tab: {e}")
        control.shutdown_flag.set()


def heartbeat_monitor(control: MetamaskServerControl):
    """Monitors the heartbeat from the browser to ensure it is still active.

    This function runs in a separate thread and checks if the last heartbeat
    was received within the specified timeout period.
    If the heartbeat timeout is exceeded, it signals the server to shut down
    and also signals the frontend to disconnect MetaMask.
    This is crucial for detecting if the browser tab was closed or if the connection was lost.

    :param control: The MetamaskServerControl instance managing the server state.
    :type control: MetamaskServerControl
    """
    while not control.shutdown_flag.is_set():
        # Only trigger a shutdown if:
        #  - network sync is complete (switch and browser tab opened)
        #  - an account was successfully connected AND heartbeat is lost.
        if (
            control.network_sync_event.is_set()
            and control.connected_account_event.is_set()
            and (
                time.time() - control.last_heartbeat_time > control.heartbeat_timeout_s
            )
        ):
            logger.warning(
                f"\nNo heartbeat received for {control.heartbeat_timeout_s} seconds "
                f"after account {control.connected_account_address} was connected. "
                "Assuming browser closed. Shutting down server..."
            )
            control.signal_disconnect_frontend = True
            logger.info(
                "Signaling frontend to disconnect MetaMask due to heartbeat timeout."
            )
            control.shutdown_flag.set()  # Signal main thread to shut down server
            break
        time.sleep(1)


def run_http_server(port: int, ui_files_path: Path, control: MetamaskServerControl):
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


# Define the recursive conversion function
def convert_json_serializable_types(obj):
    """
    Recursively converts non-JSON-serializable types (like HexBytes, bytes)
    into JSON-serializable strings (0x-prefixed hex).
    """
    if isinstance(obj, (bytes, HexBytes)):
        return encode_hex(obj)
    elif isinstance(obj, dict):
        return {k: convert_json_serializable_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_json_serializable_types(elem) for elem in obj]
    return obj
