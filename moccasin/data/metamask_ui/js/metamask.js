// js/metamask.js
// Handles direct interactions with the MetaMask provider (window.ethereum).

import { setStatus, showSpinner, hideSpinner } from "./ui.js";
import {
  reportTransactionResult,
  reportAccountConnectionStatus,
} from "./api.js";
import { state } from "./state.js";

/**
 * Checks if MetaMask is available.
 * @returns {boolean}
 */
export function isMetaMaskAvailable() {
  return typeof window.ethereum !== "undefined";
}

/**
 * Gets the current chain ID from MetaMask.
 * @returns {Promise<number|null>} - Returns the chain ID as an integer, or null if not available/error.
 */
export async function getMetaMaskChainId() {
  if (!isMetaMaskAvailable()) return null;
  try {
    const chainIdHex = await window.ethereum.request({ method: "eth_chainId" });
    return parseInt(chainIdHex, 16); // Convert hex string to integer
  } catch (error) {
    console.error("Error getting MetaMask chainId:", error);
    return null;
  }
}

/**
 * Requests accounts from MetaMask.
 * Sets state.currentAccount and state.isMetaMaskConnected on success.
 * @returns {Promise<boolean>} - True if accounts are successfully connected, false otherwise.
 */
export async function requestMetaMaskAccounts() {
  if (!isMetaMaskAvailable()) {
    return false;
  }
  try {
    const accounts = await window.ethereum.request({
      method: "eth_requestAccounts",
    });
    if (accounts.length > 0) {
      state.currentAccount = accounts[0];
      state.isMetaMaskConnected = true;
      // Report success
      await reportAccountConnectionStatus(state.currentAccount, "connected");
      return true;
    } else {
      setStatus("No accounts returned from MetaMask.", "error");
      state.currentAccount = null;
      state.isMetaMaskConnected = false;
      await reportAccountConnectionStatus(null, "error");
      return false;
    }
  } catch (error) {
    state.currentAccount = null;
    state.isMetaMaskConnected = false;

    if (error.code === 4001) {
      setStatus(
        "MetaMask connection rejected by user. Shutting down.",
        "error"
      ); // Update UI message
      await reportAccountConnectionStatus(null, "rejected");
    } else {
      setStatus(`MetaMask connection error: ${error.message}`, "error");
      await reportAccountConnectionStatus(null, "error");
    }
    return false;
  }
}

/**
 * Sends a transaction via MetaMask.
 * @param {Object} txParams - Transaction parameters.
 * @returns {Promise<string|null>} - Transaction hash on success, null on failure/rejection.
 */
export async function sendMetaMaskTransaction(txParams) {
  if (!isMetaMaskAvailable()) {
    return null;
  }
  try {
    // Ensure 'from' address matches connected account (MetaMask often enforces this)
    if (
      txParams.from &&
      txParams.from.toLowerCase() !== state.currentAccount.toLowerCase()
    ) {
      console.warn(
        `Transaction 'from' address mismatch. Overwriting with connected account: ${state.currentAccount}`
      );
      txParams.from = state.currentAccount;
    }
    setStatus("Please confirm transaction in MetaMask...", "default");
    showSpinner();
    const txHash = await window.ethereum.request({
      method: "eth_sendTransaction",
      params: [txParams],
    });
    console.log("Transaction sent. Hash: " + txHash);
    return txHash;
  } catch (txError) {
    hideSpinner();
    console.error("MetaMask transaction error:", txError);

    let errorMessage = txError.message || "Unknown transaction error.";
    let errorCode = txError.code || "UNKNOWN_CODE";
    let statusForBackend = "error"; // Default status for backend

    if (txError.code === 4001) {
      setStatus("Transaction rejected by user.", "error");
      errorMessage = "Transaction rejected by user.";
      statusForBackend = "rejected"; // More specific status for user rejection
    } else if (txError.code === -32603) {
      setStatus(
        `Transaction error: ${txError.message}. Check gas limit or funds.`,
        "error"
      );
    } else {
      setStatus(`Transaction failed: ${txError.message}`, "error");
    }

    // Report the transaction failure/rejection to the backend immediately
    await reportTransactionResult({
      status: statusForBackend, // "rejected" or "error"
      error: errorMessage,
      code: errorCode,
      txParams: txParams, // Include original txParams for context
    });

    return null;
  }
}

/**
 * Polls for the transaction receipt using the transaction hash.
 * @param {string} txHash - The transaction hash.
 * @param {number} maxAttempts - Maximum number of polling attempts.
 * @param {number} delay - Delay between attempts in milliseconds.
 * @returns {Promise<Object|null>} - Transaction receipt on success, null on timeout/error.
 */
export async function pollForTransactionReceipt(
  txHash,
  maxAttempts = 60,
  delay = 5000
) {
  if (!isMetaMaskAvailable()) return null;
  let attempts = 0;
  while (attempts < maxAttempts) {
    try {
      const receipt = await window.ethereum.request({
        method: "eth_getTransactionReceipt",
        params: [txHash],
      });
      if (receipt) {
        if (receipt.status === "0x0") {
          throw new Error(`Transaction reverted on chain: ${txHash}`);
        }
        return receipt;
      }
    } catch (error) {
      console.warn(
        `Error getting receipt for ${txHash} (attempt ${
          attempts + 1
        }/${maxAttempts}): ${error.message}`
      );
      if (error.code === -32000) {
        // Common error for transaction not found yet
        // Continue polling
      } else {
        // Other errors might indicate a problem, stop polling
        console.error("Irrecoverable error during receipt polling:", error);
        return null;
      }
    }
    attempts++;
    await new Promise((resolve) => setTimeout(resolve, delay));
  }
  setStatus(`Timeout waiting for transaction receipt: ${txHash}`, "error");
  return null;
}

/**
 * Revokes MetaMask permissions for the current origin.
 * @returns {Promise<void>}
 */
export async function revokeMetaMaskPermissions() {
  if (!isMetaMaskAvailable()) {
    console.log("MetaMask not available, no permissions to revoke.");
    return;
  }
  try {
    await window.ethereum.request({
      method: "wallet_revokePermissions",
      params: [{ eth_accounts: {} }],
    });
    console.log("MetaMask permissions revoked.");
  } catch (error) {
    console.error("Error revoking MetaMask permissions:", error);
  }
}
