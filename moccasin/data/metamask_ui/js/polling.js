// js/polling.js
// Manages all polling intervals.

import * as api from "./api.js"; // Import all API functions
import * as metamask from "./metamask.js"; // Import all MetaMask functions
import { state } from "./state.js"; // Access global state
import { setStatus, setInstructions, hideSpinner } from "./ui.js"; // For direct UI updates from intervals

const HEARTBEAT_INTERVAL_CLIENT_MS = 5000;
const DISCONNECT_POLLING_INTERVAL_MS = 2000;
const TRANSACTION_POLLING_INTERVAL_MS = 1000;
const ACCOUNT_STATUS_POLLING_INTERVAL_MS = 2000;

let heartbeatInterval = null;
let transactionPollingInterval = null;
let accountStatusInterval = null;
let disconnectPollingInterval = null;

// Callback function to be set by main.js for disconnect events
let onAppDisconnectCallback = null;

/**
 * Sets the callback function to be invoked when a disconnect signal is received.
 * @param {Function} callback - The function to call on disconnect.
 */
export function setOnAppDisconnectCallback(callback) {
  onAppDisconnectCallback = callback;
}

// --- Heartbeat Polling ---
async function handleHeartbeat() {
  const ok = await api.sendHeartbeat();
  if (!ok) {
    // Trigger main app disconnect through callback
    if (onAppDisconnectCallback) {
      onAppDisconnectCallback();
    } else {
      stopAllIntervals(); // Fallback if no callback
    }
  }
}

export function startHeartbeatPolling() {
  if (!heartbeatInterval) {
    heartbeatInterval = setInterval(
      handleHeartbeat,
      HEARTBEAT_INTERVAL_CLIENT_MS
    );
    console.log("Started heartbeat polling.");
  }
}

export function stopHeartbeatPolling() {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval);
    heartbeatInterval = null;
    console.log("Stopped heartbeat polling.");
  }
}

// --- Disconnect Signal Polling ---
async function handleDisconnectSignal() {
  const result = await api.pollForDisconnectSignal();
  if (result.disconnect) {
    console.warn(
      "Received disconnect signal from Python backend. Initiating frontend disconnect..."
    );
    if (onAppDisconnectCallback) {
      onAppDisconnectCallback();
    } else {
      stopAllIntervals();
    }
  } else if (result.backend_unreachable) {
    console.error(
      "Backend unreachable during disconnect signal check. Initiating disconnect."
    );
    if (onAppDisconnectCallback) {
      onAppDisconnectCallback();
    } else {
      stopAllIntervals();
    }
  }
}

export function startDisconnectPolling() {
  if (!disconnectPollingInterval) {
    disconnectPollingInterval = setInterval(
      handleDisconnectSignal,
      DISCONNECT_POLLING_INTERVAL_MS
    );
    console.log("Started disconnect signal polling.");
  }
}

export function stopDisconnectPolling() {
  if (disconnectPollingInterval) {
    clearInterval(disconnectPollingInterval);
    disconnectPollingInterval = null;
    console.log("Stopped disconnect signal polling.");
  }
}

// --- Account Status Polling ---
async function handleAccountStatusCheck() {
  if (!state.isMetaMaskConnected || !state.currentAccount) {
    stopAccountStatusPolling(); // Stop if no account connected
    return;
  }
  const accountStatus = await api.checkAccountStatus();
  if (!accountStatus.ok && accountStatus.error === "zero_balance") {
    setStatus("Connected wallet has 0 gas!", "error");
    setInstructions(`
      <p>The account <strong>${accountStatus.current_address}</strong> has <strong>zero balance</strong>.</p>
      <p>Please connect to an account with funds in MetaMask.</p>
      <p>You can <strong>go to MetaMask</strong> and switch accounts or add funds to the current account.</p>
    `);
    stopTransactionPolling(); // Stop transaction polling if no gas
  } else if (
    !accountStatus.ok &&
    accountStatus.error === "backend_unreachable"
  ) {
    console.error(
      "Backend unreachable during account status check. Initiating disconnect."
    );
    if (onAppDisconnectCallback) {
      onAppDisconnectCallback();
    } else {
      stopAllIntervals();
    }
  } else if (accountStatus.ok) {
    // Account status is good, stop this polling and start transaction polling
    stopAccountStatusPolling();
    setStatus(
      "Account connected successfully! Waiting for transactions...",
      "success"
    );
    setInstructions(
      "<p>Account has balance. Waiting for transactions from your script...</p>"
    );
    startTransactionPolling();
  }
}

export function startAccountStatusPolling() {
  if (!accountStatusInterval) {
    handleAccountStatusCheck(); // Run once immediately
    accountStatusInterval = setInterval(
      handleAccountStatusCheck,
      ACCOUNT_STATUS_POLLING_INTERVAL_MS
    );
    console.log("Started account status polling.");
  }
}

export function stopAccountStatusPolling() {
  if (accountStatusInterval) {
    clearInterval(accountStatusInterval);
    accountStatusInterval = null;
    console.log("Stopped account status polling.");
  }
}

// --- Transaction Polling ---
async function handleTransactionPolling() {
  if (!state.isMetaMaskConnected || !state.currentAccount) {
    stopTransactionPolling();
    return;
  }

  const txParams = await api.fetchPendingTransaction();
  if (txParams) {
    const txHash = await metamask.sendMetaMaskTransaction(txParams);
    if (txHash) {
      setStatus(
        `Transaction sent. Hash: ${txHash}. Waiting for receipt...`,
        "default"
      );
      const receipt = await metamask.pollForTransactionReceipt(txHash);
      hideSpinner(); // Hide spinner after tx confirmation or rejection

      if (receipt) {
        const contractAddress = receipt.contractAddress || null;
        await api.reportTransactionResult({
          status: "success",
          hash: txHash,
          contractAddress: contractAddress,
          receipt: receipt,
        });
        setStatus("Transaction confirmed and processed.", "success");
      } else {
        // Receipt polling failed or transaction reverted (handled in pollForTransactionReceipt)
        await api.reportTransactionResult({
          status: "error",
          error: "Transaction failed or timed out during receipt polling.",
          hash: txHash,
        });
      }
    } else {
      console.log(
        "Transaction was rejected or failed during send, already reported."
      );
    }
  }
}

export function startTransactionPolling() {
  if (!transactionPollingInterval) {
    transactionPollingInterval = setInterval(
      handleTransactionPolling,
      TRANSACTION_POLLING_INTERVAL_MS
    );
    console.log("Started transaction polling.");
  }
}

export function stopTransactionPolling() {
  if (transactionPollingInterval) {
    clearInterval(transactionPollingInterval);
    transactionPollingInterval = null;
    console.log("Stopped transaction polling.");
  }
}

/**
 * Stops all active polling intervals.
 */
export function stopAllIntervals() {
  stopHeartbeatPolling();
  stopTransactionPolling();
  stopAccountStatusPolling();
  stopDisconnectPolling();
  console.log("All polling intervals stopped.");
}
