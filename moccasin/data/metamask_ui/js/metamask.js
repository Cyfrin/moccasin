// Handles direct interactions with the MetaMask provider (window.ethereum).

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
    // You might want to set a 'not available' status here
    return false;
  }
  try {
    const accounts = await window.ethereum.request({
      method: "eth_requestAccounts",
    });
    if (accounts.length > 0) {
      state.currentAccount = accounts[0];
      state.isMetaMaskConnected = true;
      await reportAccountConnectionStatus(state.currentAccount, "connected");
      return true;
    } else {
      state.currentAccount = null;
      state.isMetaMaskConnected = false;
      await reportAccountConnectionStatus(null, "error");
      return false;
    }
  } catch (error) {
    state.currentAccount = null;
    state.isMetaMaskConnected = false;

    if (error.code === 4001) {
      await reportAccountConnectionStatus(null, "rejected");
    } else {
      await reportAccountConnectionStatus(null, "error");
    }
    return false;
  }
}

/**
 * Sends a transaction via MetaMask.
 *
 * @param {Object} txParams - Transaction parameters.
 * @returns {Promise<string|null>} - Transaction hash on success, null on failure/rejection.
 * @dev This function *still* reports results immediately because transaction *sending*
 * can fail before a receipt is even available for polling.
 */
export async function sendMetaMaskTransaction(txParams) {
  if (!isMetaMaskAvailable()) {
    // Ideally, polling should prevent this call if MetaMask isn't available.
    // Consider throwing an error here instead of returning null for cleaner error propagation.
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
    const txHash = await window.ethereum.request({
      method: "eth_sendTransaction",
      params: [txParams],
    });
    console.log("Transaction sent. Hash: " + txHash);
    return txHash;
  } catch (txError) {
    console.error("MetaMask transaction error:", txError);

    let errorMessage = txError.message || "Unknown transaction error.";
    let errorCode = txError.code || "UNKNOWN_CODE";
    let statusForBackend = "error";

    if (txError.code === 4001) {
      errorMessage = "Transaction rejected by user.";
      statusForBackend = "rejected";
    }

    // Report the transaction sending failure/rejection to the backend immediately.
    // This is important because the polling module relies on txHash being non-null
    // to continue to receipt polling. If sending fails, we need to report that.
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
 * Requests a signature via MetaMask for either a personal message or typed data.
 *
 * @param {string} requestMethod - The MetaMask RPC method to use ("personal_sign" or "eth_signTypedData_v4").
 * @param {string} account - The account to sign from.
 * @param {string|object} dataToSign - The message string for personal_sign, or the EIP-712 typed data object for eth_signTypedData_v4.
 * @returns {Promise<string>} - The signature on success.
 * @throws {Error} - Throws an error object if signing fails or is rejected by the user.
 */
export async function signWithMetaMask(requestMethod, account, dataToSign) {
  if (!isMetaMaskAvailable()) {
    throw new Error("MetaMask is not available."); // Throw instead of returning null for clarity
  }
  try {
    let signature;

    if (requestMethod === "eth_signTypedData_v4") {
      console.log("Requesting eth_signTypedData_v4 with payload:", dataToSign);
      signature = await window.ethereum.request({
        method: "eth_signTypedData_v4",
        params: [account, dataToSign], // dataToSign must be the EIP-712 object
      });
    } else if (requestMethod === "personal_sign") {
      console.log("Requesting personal_sign with message:", dataToSign);
      signature = await window.ethereum.request({
        method: "personal_sign",
        params: [dataToSign, account], // Order for personal_sign is message, account
      });
    } else {
      throw new Error(`Unsupported signing method: ${requestMethod}`);
    }

    console.log("Message signed. Signature: " + signature);
    return signature; // Return signature on success
  } catch (signError) {
    console.error("MetaMask signing error (propagating):", signError);
    throw signError; // Re-throw the error so polling.js can catch and handle it.
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
  // Removed setStatus: Polling module will manage UI for the final outcome
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
