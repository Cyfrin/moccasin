// Manages all polling intervals.

import * as api from "./api.js";
import * as metamask from "./metamask.js";
import { state } from "./state.js";
import { setStatus, setInstructions, showSpinner, hideSpinner } from "./ui.js";

const HEARTBEAT_INTERVAL_CLIENT_MS = 5000;
const DISCONNECT_POLLING_INTERVAL_MS = 2000;
const TRANSACTION_POLLING_INTERVAL_MS = 1000;
const MESSAGE_SIGNING_POLLING_INTERVAL_MS = 1000;
const ACCOUNT_STATUS_POLLING_INTERVAL_MS = 2000;

let heartbeatInterval = null;
let transactionPollingInterval = null;
let messageSigningPollingInterval = null;
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

// ################################################################
// #                      HEARTBEAT POLLING                       #
// ################################################################
/**
 * Handles the heartbeat check with the backend.
 * If the heartbeat fails, it triggers the application disconnect process.
 */
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

/**
 * Starts the heartbeat polling interval.
 * This periodically checks if the backend server is responsive.
 */
export function startHeartbeatPolling() {
  if (!heartbeatInterval) {
    heartbeatInterval = setInterval(
      handleHeartbeat,
      HEARTBEAT_INTERVAL_CLIENT_MS
    );
    console.log("Started heartbeat polling.");
  }
}

/**
 * Stops the heartbeat polling interval.
 */
export function stopHeartbeatPolling() {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval);
    heartbeatInterval = null;
    console.log("Stopped heartbeat polling.");
  }
}

// ################################################################
// #                  DISCONNECT SIGNAL POLLING                   #
// ################################################################
/**
 * Handles the disconnect signal check with the backend.
 * If a disconnect signal is received or the backend is unreachable,
 * it triggers the application disconnect process.
 */
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

/**
 * Starts the disconnect signal polling interval.
 * This periodically checks if the backend has signaled for a disconnect.
 */
export function startDisconnectPolling() {
  if (!disconnectPollingInterval) {
    disconnectPollingInterval = setInterval(
      handleDisconnectSignal,
      DISCONNECT_POLLING_INTERVAL_MS
    );
    console.log("Started disconnect signal polling.");
  }
}

/**
 * Stops the disconnect signal polling interval.
 */
export function stopDisconnectPolling() {
  if (disconnectPollingInterval) {
    clearInterval(disconnectPollingInterval);
    disconnectPollingInterval = null;
    console.log("Stopped disconnect signal polling.");
  }
}

// ################################################################
// #                    ACCOUNT STATUS POLLING                    #
// ################################################################
/**
 * Handles the account status check.
 * It verifies if MetaMask is connected, if the current account has a balance,
 * and handles backend unreachability.
 * Based on the status, it updates the UI and may start/stop other polling.
 */
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
    stopMessageSigningPolling(); // Stop message signing polling too
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
    startMessageSigningPolling();
    startTransactionPolling();
  }
}

/**
 * Starts the account status polling interval.
 * It runs an initial check immediately and then polls periodically.
 */
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

/**
 * Stops the account status polling interval.
 */
export function stopAccountStatusPolling() {
  if (accountStatusInterval) {
    clearInterval(accountStatusInterval);
    accountStatusInterval = null;
    console.log("Stopped account status polling.");
  }
}

// ################################################################
// #                     TRANSACTION POLLING                      #
// ################################################################
/**
 * Handles polling for pending transactions from the backend.
 * If a transaction is found, it sends it via MetaMask, polls for the receipt,
 * and reports the result back to the backend.
 */
async function handleTransactionPolling() {
  if (!state.isMetaMaskConnected || !state.currentAccount) {
    stopTransactionPolling();
    return;
  }

  const txParams = await api.fetchPendingTransaction();
  if (txParams) {
    setStatus("Please confirm transaction in MetaMask...", "default");
    showSpinner();
    const txHash = await metamask.sendMetaMaskTransaction(txParams);
    hideSpinner();

    if (txHash) {
      // Transaction was sent successfully (not rejected/failed during send)
      setStatus(
        `Transaction sent. Hash: ${txHash}. Waiting for receipt...`,
        "default"
      );
      // No spinner here as we're just waiting for receipt from the blockchain
      const receipt = await metamask.pollForTransactionReceipt(txHash);

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
        setStatus(
          `Timeout waiting for transaction receipt: ${txHash}`,
          "error"
        );
        await api.reportTransactionResult({
          status: "error",
          error: "Transaction failed or timed out during receipt polling.",
          hash: txHash,
        });
      }
    } else {
      // If txHash is null, it means sendMetaMaskTransaction already reported a rejection/error
      // to the backend, and handled its own UI via the reportTransactionResult call within it.
      console.log(
        "Transaction was rejected or failed during send, already reported."
      );
    }
  }
}

/**
 * Starts the transaction polling interval.
 * This periodically checks the backend for new transactions to process.
 */
export function startTransactionPolling() {
  if (!transactionPollingInterval) {
    transactionPollingInterval = setInterval(
      handleTransactionPolling,
      TRANSACTION_POLLING_INTERVAL_MS
    );
    console.log("Started transaction polling.");
  }
}

/**
 * Stops the transaction polling interval.
 */
export function stopTransactionPolling() {
  if (transactionPollingInterval) {
    clearInterval(transactionPollingInterval);
    transactionPollingInterval = null;
    console.log("Stopped transaction polling.");
  }
}

// ################################################################
// #                   MESSAGE SIGNING POLLING                    #
// ################################################################
/**
 * Handles polling for pending message signing requests from the backend.
 * If a request is found, it prompts the user to sign the message via MetaMask
 * and reports the result back to the backend.
 */
async function handleMessageSigningPolling() {
  if (!state.isMetaMaskConnected || !state.currentAccount) {
    stopMessageSigningPolling(); // Stop if no account connected
    return;
  }

  const signingRequest = await api.fetchPendingMessageSigning();
  if (signingRequest) {
    console.log("Processing signing request:", signingRequest);

    const { type: requestType, account, payload, message } = signingRequest; // Destructure the request

    let dataToSign;
    if (requestType === "eth_signTypedData_v4") {
      dataToSign = payload; // Payload holds the EIP-712 object
    } else if (requestType === "personal_sign") {
      dataToSign = message; // Message holds the simple string
    } else {
      console.error(`Received unknown signing request type: ${requestType}`);
      // Report this error back to backend immediately if the type is unknown
      await api.reportMessageSigningResult({
        status: "error",
        error: `Unknown signing request type: ${requestType}`,
        code: "UNKNOWN_TYPE_ERROR",
        requestMethod: requestType,
        payload: payload, // Send original payload/message for debugging
        message: message,
      });
      return; // Stop processing this request
    }

    let signature = null;
    let errorToReport = null;
    let errorCodeToReport = null;

    try {
      setStatus("Please sign the message in MetaMask...", "default");
      showSpinner();

      // Call the MetaMask signing function.
      // This will now throw an error if rejected or failed.
      signature = await metamask.signWithMetaMask(
        requestType,
        account,
        dataToSign
      );

      // If execution reaches here, signing was successful
      setStatus("Message signed successfully!", "success");
      await api.reportMessageSigningResult({
        status: "success",
        signature: signature,
        requestMethod: requestType,
        payload: payload,
        message: message,
      });
    } catch (e) {
      console.error(`Error during MetaMask message signing: ${e.message || e}`);
      errorToReport = e.message;

      // Extract specific error code if available from MetaMask error object
      // MetaMask's user rejection error code is commonly 4001
      if (e.code) {
        errorCodeToReport = e.code;
      }

      // Set UI status based on error type
      if (errorCodeToReport === 4001) {
        setStatus(
          "Signing rejected by user. Please restart if needed.",
          "error"
        );
        errorToReport = "Signing rejected by user."; // More explicit message for backend
      } else {
        setStatus(`Message signing failed: ${errorToReport}`, "error");
      }

      await api.reportMessageSigningResult({
        status: "error",
        error: errorToReport,
        code: errorCodeToReport,
        requestMethod: requestType,
        payload: payload, // Include original payload/message for debugging
        message: message,
      });
    } finally {
      hideSpinner();
    }
  }
}

/**
 * Starts the message signing polling interval.
 * This periodically checks the backend for new messages to sign.
 */
export function startMessageSigningPolling() {
  if (!messageSigningPollingInterval) {
    messageSigningPollingInterval = setInterval(
      handleMessageSigningPolling,
      MESSAGE_SIGNING_POLLING_INTERVAL_MS
    );
    console.log("Started message signing polling.");
  }
}

/**
 * Stops the message signing polling interval.
 */
export function stopMessageSigningPolling() {
  if (messageSigningPollingInterval) {
    clearInterval(messageSigningPollingInterval);
    messageSigningPollingInterval = null;
    console.log("Stopped message signing polling.");
  }
}

/**
 * Stops all active polling intervals.
 */
export function stopAllIntervals() {
  stopMessageSigningPolling();
  stopHeartbeatPolling();
  stopTransactionPolling();
  stopAccountStatusPolling();
  stopDisconnectPolling();
  console.log("All polling intervals stopped.");
}
