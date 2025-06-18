import importlib.resources
import threading
import time
from typing import Any, Dict

from moccasin.logging import logger
from moccasin.metamask_cli_integration.constants import (
    ACCOUNT_CONNECTION_TIMEOUT_S,
    NETWORK_SYNC_TIMEOUT_S,
)
from moccasin.metamask_cli_integration.server_control import (
    MetamaskServerControl,
    set_server_control,
)
from moccasin.metamask_cli_integration.utils import (
    heartbeat_monitor,
    open_browser_tab,
    run_http_server,
)


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
        target=run_http_server, args=(PORT, ui_files_path, control)
    )
    control.server_thread.daemon = (
        True  # @dev daemon thread will exit when the main program exits
    )
    control.server_thread.start()

    # Wait a moment to ensure the server is ready before opening the browser
    time.sleep(0.5)

    # Start the heartbeat monitor thread to check for browser activity
    control.monitor_thread = threading.Thread(target=heartbeat_monitor, args=(control,))
    control.monitor_thread.daemon = True
    control.monitor_thread.start()

    # Open browser to start network sync process
    logger.info("Opening in existing browser session.")
    control.browser_thread = threading.Thread(target=open_browser_tab, args=(PORT,))
    control.browser_thread.daemon = True
    control.browser_thread.start()

    logger.info(
        "MetaMask UI launched. Please check the browser window for network synchronization."
    )
    logger.info(f"If the tab didn't open, visit http://localhost:{PORT}/index.html")

    # Wait for the browser to signal that the MetaMask network is synced
    logger.info("Waiting for MetaMask network synchronization...")
    if not control.network_sync_event.wait(timeout=NETWORK_SYNC_TIMEOUT_S):
        # If the network sync event is not set within the timeout, log an error and stop the server
        logger.error(
            "Timed out waiting for MetaMask network synchronization. Please ensure MetaMask is connected and the page is open."
        )
        stop_metamask_ui_server(control)
        raise TimeoutError("MetaMask network synchronization timed out.")

    # Then wait for MetaMask account connection (if not already received during sync)
    # This part should be called *after* network sync, as account connection might depend on it.
    if not control.connected_account_address:
        logger.info(
            "MetaMask network synced. Waiting for account connection or user rejection..."
        )
        control.connected_account_event.wait(timeout=ACCOUNT_CONNECTION_TIMEOUT_S)

    # Now, check the status
    if control.connected_account_address:
        logger.info(f"MetaMask account connected: {control.connected_account_address}")
        return control  # Success, return control
    elif control.user_declined_account_connection:
        logger.error(
            "MetaMask account connection explicitly rejected by user. Shutting down server."
        )
        stop_metamask_ui_server(control)
        # Raise an error to indicate the reason for shutdown, so the calling process knows
        raise RuntimeError(
            "MetaMask account connection declined by user, server shutting down."
        )
    else:
        # This means connected_account_address is None and user_declined_account_connection is False
        # which implies a genuine timeout without explicit rejection.
        logger.error(
            "Timed out waiting for MetaMask account connection. Ensure account is connected."
        )
        stop_metamask_ui_server(control)
        raise TimeoutError("MetaMask account connection timed out after network sync.")


def stop_metamask_ui_server(control: MetamaskServerControl):
    """Gracefully stops the MetaMask UI server.

    This function signals the server to shut down, closes the HTTP server,
    and cleans up any resources used by the server control.
    It also sets a flag to signal the frontend to disconnect MetaMask.

    :param control: The MetamaskServerControl instance managing the server state.
    :type control: MetamaskServerControl
    """
    if control:
        # Signal the frontend to disconnect MetaMask before shutting down the server
        control.signal_disconnect_frontend = True
        logger.info("Signaled frontend to disconnect MetaMask.")
        # Give the frontend a moment to process the disconnect signal if it's polling
        time.sleep(1)  # Small delay

        if control.httpd:
            control.shutdown_flag.set()
            control.httpd.shutdown()
            control.httpd.server_close()
            logger.debug("MetaMask UI server gracefully stopped and closed.")
        else:
            logger.debug("MetaMask UI server not running or already stopped.")
    else:
        logger.debug("No MetamaskServerControl instance to stop.")
