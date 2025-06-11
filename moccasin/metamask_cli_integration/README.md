# `moccasin.metamask_cli_integration` Module

This module provides a robust and decoupled integration layer for the Moccasin CLI to interact with MetaMask. It enables users to delegate transaction signing and account management to the MetaMask browser extension, enhancing security by avoiding direct private key handling within the CLI.

## Purpose

The primary goal of this module is to abstract the complexities of communicating with the MetaMask UI. It establishes a local HTTP server that acts as a bridge, allowing the Moccasin CLI to:

- **Launch and manage a MetaMask UI tab:** Provides a user-friendly interface for network synchronization and account connection.

- **Delegate transaction signing:** Pushes transaction requests to MetaMask for user confirmation.

- **Receive transaction results:** Captures broadcasted transaction hashes or error messages from MetaMask.

- **Monitor connection status:** Utilizes a heartbeat mechanism to detect if the browser tab is closed unexpectedly.

## Module Structure

The `metamask_cli_integration` module is carefully organized into several smaller, focused files to enhance clarity, maintainability, and testability:

```bash
    moccasin/metamask_cli_integration/
    ├── init.py
    ├── constants.py
    ├── server_control.py
    ├── http_handler.py
    ├── account.py
    ├── utils.py
    └── server_lifecycle.py
```

## Key Components

- **`MetamaskServerControl` (in `server_control.py`):** The central state management object. It holds queues for inter-thread communication (CLI ↔ Browser), synchronization events, and server status flags.

- **`CustomHandler` (in `http_handler.py`):** An extension of Python's `SimpleHTTPRequestHandler`, responsible for serving static UI files and handling specific API endpoints for MetaMask interactions (e.g., `heartbeat`, `report_transaction_result`, `api/network-synced`).

- **`MetaMaskAccount` (in `account.py`):** A custom account class that implements the `send_transaction` and `sign_typed_data` methods. It interacts with the MetaMask UI to sign transactions and typed data, returning results or errors as needed.

- **Lifecycle Functions (in `server_lifecycle.py`):**

  - `start_metamask_ui_server()`: Initializes the server, launches the browser UI, and manages the network synchronization and account connection flow with appropriate timeouts.

  - `stop_metamask_ui_server()`: Gracefully shuts down the server and signals the frontend to disconnect.

- **Heartbeat Monitoring (`heartbeat_monitor` in `utils.py`):** Ensures the browser tab is still active. It only triggers a shutdown warning if the connection is lost _after_ an account has been successfully connected, preventing premature errors during initial setup.

- **Constants (`constants.py`):** All timeouts and fixed values are defined here for easy configuration and readability.
