# Moccasin CLI DApp UI (`data/metamask_ui`)

This directory (`data/metamask_ui`) contains the frontend user interface for the Moccasin Command Line Interface (CLI) DApp. It's designed to be served by a Python backend and facilitates interaction with MetaMask for various blockchain operations required by the CLI script.

Here are the Python backend files that support this UI:

```bash
    moccasin
    ├── metamask_integration.py
    └── _sys_path_and_config_setup.py
```

The UI is built with a modular JavaScript architecture to ensure maintainability, prevent circular dependencies, and provide clear separation of concerns.

> &#x1F4A1; We use Vanilla JavaScript to avoid any external dependencies like React or Vue.js, keeping the DApp lightweight and easy to integrate with the Moccasin CLI in Python.

---

## Folder Structure

```bash
    data/
    └── metamask_ui/
    │   ├── index.html
    │   └── js/
    │       ├── api.js
    │       ├── elements.js
    │       ├── main.js
    │       ├── metamask.js
    │       ├── polling.js
    │       ├── state.js
    │       └── ui.js
    └── README.md  <-- This file
```

---

## Summary of Key Files

### `index.html`

This is the main entry point for the DApp's user interface. It's a standard HTML file that:

- Sets up the basic page structure.
- Includes inline CSS for **sick** Moccasin styling.
- Contains the core UI elements: a status message area, an instructions area, and interactive buttons (e.g., for switching networks, continuing script).
- Loads `js/main.js` as a JavaScript module, which bootstraps the entire DApp frontend.

### `js` Directory

This directory contains all the modular JavaScript files that power the DApp's frontend logic. The design emphasizes a clear hierarchy to manage dependencies effectively.

#### `js/elements.js`

- **Purpose:** Centralizes all references to HTML DOM elements (e.g., `statusElement`).
- **Role:** Acts as the lowest layer in the UI stack, providing a single source for element access to prevent redundant `document.getElementById()` calls across modules.
- **Dependencies:** None.

#### `js/ui.js`

- **Purpose:** Provides a set of utility functions for manipulating the DApp's user interface.
- **Role:** Handles all visual updates, such as setting status messages, displaying instructions, showing/hiding spinners, and controlling button visibility. It uses the element references from `elements.js`.
- **Dependencies:** Imports from `elements.js`.

#### `js/state.js`

- **Purpose:** Manages the global application state.
- **Role:** Stores shared data like the `currentAccount`, `isMetaMaskConnected` status, `isDisconnecting` flasg, and `boaNetworkDetails` (details of the target blockchain network provided by the CLI). It uses getters and setters to provide a controlled way to access and update this state. This module is crucial for breaking circular dependencies by centralizing data.
- **Dependencies:** None.

#### `js/api.js`

- **Purpose:** Handles all communication with the Python backend of the Moccasin CLI.
- **Role:** Contains asynchronous functions for making `fetch` requests to specific backend API endpoints (e.g., `getBoaNetworkDetails`, `reportAccountConnectionStatus`, `sendHeartbeat`, `fetchPendingTransaction`, `reportTransactionResult`). It provides status updates to the UI using functions from `ui.js`.
- **Dependencies:** Imports from `ui.js` (for status updates) and `state.js` (to read/update global state related to API responses).

#### `js/metamask.js`

- **Purpose:** Encapsulates all direct interactions with the MetaMask browser extension (`window.ethereum`).
- **Role:** Provides functions for blockchain-related operations that require MetaMask, such as getting the current chain ID, requesting accounts, switching networks, sending transactions, polling for transaction receipts, and revoking permissions. It uses `ui.js` for MetaMask-specific prompts (e.g., "confirm transaction") and `api.js` to report account connections to the backend.
- **Dependencies:** Imports from `ui.js`, `api.js`, and `state.js`.

#### `js/polling.js`

- **Purpose:** Manages all interval-based background tasks.
- **Role:** Sets up and clears `setInterval` timers for continuous polling operations:
  - **Heartbeat:** Checks if the Python backend is still alive.
  - **Disconnect Signal:** Polls the backend for a signal to disconnect the DApp.
  - **Account Status:** Periodically checks the connected account's status (e.g., balance) via the backend.
  - **Transaction Polling:** Fetches pending transaction requests from the backend and initiates MetaMask transactions.
- **Communication:** When a critical event (like a disconnect signal or backend unreachability) is detected, it notifies `main.js` via a registered callback function, allowing `main.js` to orchestrate a full application disconnect.
- **Dependencies:** Imports from `api.js`, `metamask.js`, `state.js`, and `ui.js` (for direct status updates related to polling).

#### `js/main.js`

- **Purpose:** The central orchestrator and entry point for the entire frontend application.
- **Role:**
  - Initializes the DApp on `DOMContentLoaded`.
  - Sets up all global event listeners (e.g., `MetaMask accountsChanged`, `chainChanged`, `disconnect`).
  - Contains the core `updateUI()` logic, which evaluates the current state (MetaMask availability, network match, account connection) and orchestrates calls to other modules (`api.js`, `metamask.js`, `polling.js`, `ui.js`) to transition the DApp through its various states.
  - Handles the comprehensive `disconnectApp()` process, coordinating cleanup across all modules.
  - Acts as the "controller" that binds together the "model" (state, api, metamask) and "view" (ui, elements) components.
- **Dependencies:** Imports from `ui.js`, `elements.js`, `api.js`, `metamask.js`, `polling.js`, and `state.js`. It ties everything together.
