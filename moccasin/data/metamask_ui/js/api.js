// js/api.js
// Handles all communication with the Python backend.

import { setInstructions, setStatus } from "./ui.js";
import { state } from "./state.js"; // To update boaNetworkDetails directly here

/**
 * Fetches the active network details from the Python backend.
 * Updates the global state.boaNetworkDetails.
 * @returns {Promise<boolean>} - True if details fetched successfully, false otherwise.
 */
export async function getBoaNetworkDetails() {
  try {
    const response = await fetch("/api/boa-network-details");
    if (!response.ok) {
      console.error(`HTTP error! status: ${response.status}`);
      throw new Error(
        `Failed to fetch Boa network details: ${response.status}`
      );
    }
    const data = await response.json();
    state.boaNetworkDetails = {
      chainId: parseInt(data.chainId), // Convert to integer for comparison
      rpcUrl: data.rpcUrl,
      networkName: data.networkName,
    };
    return true;
  } catch (error) {
    console.error("Error fetching Boa network details:", error);
    setStatus(
      "Error: Could not fetch Boa network details. Check backend server.",
      "error"
    );
    state.boaNetworkDetails = {}; // Clear details on error
    return false;
  }
}

/**
 * Signals the Python backend that the network is synchronized.
 */
export async function signalPythonBackendNetworkSynced() {
  try {
    const response = await fetch("/api/network-synced", { method: "POST" });
    if (!response.ok) {
      console.error(`HTTP error! status: ${response.status}`);
      throw new Error(`Failed to signal network synced: ${response.status}`);
    }
    console.log("Signaled Python backend that network is synced.");
    return true;
  } catch (error) {
    console.error("Failed to signal Python backend network sync:", error);
    setStatus(
      "Failed to signal backend network sync. Critical error.",
      "error"
    );
    return false;
  }
}

/**
 * Sends a heartbeat to the Python backend to check if it's still alive.
 * @returns {Promise<boolean>} - True if heartbeat successful, false otherwise.
 */
export async function sendHeartbeat() {
  try {
    const response = await fetch("/heartbeat", { method: "GET" });
    return response.ok;
  } catch (error) {
    console.error("Heartbeat failed, Python server might be down:", error);
    return false;
  }
}

/**
 * Polls the Python backend for a disconnect signal.
 * @returns {Promise<{disconnect: boolean, backend_unreachable: boolean}>}
 */
export async function pollForDisconnectSignal() {
  try {
    const response = await fetch("/api/check_disconnect_signal");
    if (!response.ok) {
      console.warn(
        "Failed to poll for disconnect signal, backend might be down."
      );
      return { disconnect: false, backend_unreachable: true };
    }
    const data = await response.json();
    return { disconnect: data.disconnect, backend_unreachable: false };
  } catch (error) {
    console.error("Error polling for disconnect signal:", error);
    return { disconnect: false, backend_unreachable: true };
  }
}

/**
 * Checks the account status (e.g., balance) from the Python backend.
 * @returns {Promise<{ok: boolean, error?: string, current_address?: string}>}
 */
export async function checkAccountStatus() {
  try {
    const response = await fetch("/check_account_status");
    if (!response.ok) {
      console.error(`Error checking account status: ${response.status}`);
      return { ok: false, error: "backend_error" };
    }
    return await response.json();
  } catch (error) {
    console.error("Network error checking account status:", error);
    return { ok: false, error: "backend_unreachable" };
  }
}

/**
 * Fetches a pending transaction request from the Python backend.
 * @returns {Promise<Object|null>} - Transaction parameters or null if no pending transaction.
 */
export async function fetchPendingTransaction() {
  try {
    const response = await fetch("/get_pending_transaction");
    if (response.status === 200) {
      return await response.json();
    } else if (response.status === 204) {
      return null; // No pending transaction
    } else {
      console.error("Error fetching transaction:", response.status);
      setStatus(`Error from CLI: ${response.status}`, "error");
      return null;
    }
  } catch (error) {
    console.error("Network error during transaction fetch:", error);
    return null;
  }
}

/**
 * Reports the transaction result to the Python backend.
 * @param {Object} result - The transaction result object.
 */
export async function reportTransactionResult(result) {
  try {
    const response = await fetch("/report_transaction_result", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(result),
    });
    if (!response.ok) {
      console.error(`Error reporting transaction result: ${response.status}`);
    } else {
      console.log("Transaction result reported to Python server.");
    }
  } catch (error) {
    console.error(
      "Network error reporting transaction result to Python:",
      error
    );
  }
}

/**
 * Reports the status of an account connection attempt to the Python backend.
 * This can include success, user rejection, or other errors.
 * @param {string|null} account - The connected MetaMask account address, or null.
 * @param {string} status - "connected", "rejected", "error", or "disconnected".
 */
export async function reportAccountConnectionStatus(account, status) {
  try {
    const accountToSend = account === null ? null : String(account);
    const response = await fetch("/report_account_connection_status", {
      // This endpoint will be used
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account: accountToSend, status: status }),
    });
    if (!response.ok) {
      console.error(
        `Error reporting account status to Python: ${response.status}`
      );
    } else {
      console.log(
        `Account connection status reported to Python server: ${status}, account: ${accountToSend}.`
      );
    }
  } catch (error) {
    console.error("Network error reporting account status to Python:", error);
  }
}
