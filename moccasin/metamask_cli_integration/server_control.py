import socketserver
import threading
import time
from queue import Queue
from typing import Any, Dict, Optional

from boa.util.abi import Address

from moccasin.metamask_cli_integration.constants import HEARTBEAT_TIMEOUT_SERVER_S


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
    :ivar signal_disconnect_frontend: Flag to signal the frontend to disconnect MetaMask.
    :vartype signal_disconnect_frontend: bool
    :ivar user_declined_account_connection: Flag indicating if the user declined to connect their account.
    :vartype user_declined_account_connection: bool
    """

    def __init__(self, port: int):
        self.port = port
        self.shutdown_flag = threading.Event()
        self.network_sync_event = threading.Event()
        self.transaction_request_queue: Queue[dict] = Queue()  # CLI -> Browser
        self.transaction_response_queue: Queue[str] = Queue()  # Browser -> CLI
        self.message_signing_request_queue: Queue[dict] = (
            Queue()
        )  # CLI -> Browser for message signing
        self.message_signing_response_queue: Queue[str] = (
            Queue()
        )  # Browser -> CLI for message signing
        self.connected_account_event = threading.Event()
        self.connected_account_address: Optional[Address] = None
        # Initialize last_heartbeat_time at a very early point, will be updated when browser opens
        self.last_heartbeat_time = time.time()
        self.httpd: Optional[socketserver.TCPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.browser_thread: Optional[threading.Thread] = None
        self.heartbeat_timeout_s = (
            HEARTBEAT_TIMEOUT_SERVER_S  # Uses the base heartbeat timeout
        )
        self.boa_network_details: Dict[str, Any] = {}
        self.account_status: Dict[str, Any] = {"ok": False}
        self.signal_disconnect_frontend: bool = False
        self.user_declined_account_connection: bool = False


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
