/**
 * Main JavaScript for MetaMask UI
 *
 * Handles MetaMask connection, network switching, transaction processing,
 * and communication with the Python backend.
 */

// --- Constants and Global Variables ---
const HEARTBEAT_INTERVAL_CLIENT_MS = 5000;

// HTML Elements
const statusElement = document.getElementById("status-message");
const instructionsElement = document.getElementById("instructions");
const switchButton = document.getElementById("switchNetworkButton");
const continueButton = document.getElementById("continueButton");
const spinnerElement = document.querySelector(".loading-spinner");

// Global state variables
let currentAccount = null; // Current connected MetaMask account
let isMetaMaskConnected = false;
let heartbeatInterval = null; // Interval for heartbeat to Python server
let pollingInterval = null; // Interval for transaction polling
let boaNetworkDetails = {}; // Details of the active network for Boa (chainId, rpcUrl, networkName)
let accountStatusInterval = null;

// --- Utility Functions for UI Updates ---
/**
 * Sets the status message in the UI with appropriate styling.
 *
 * @param {string} message - The message to display.
 * @param {string} type - The type of message ('default', 'error', 'success', 'warning').
 */
function setStatus(message, type = "default") {
  statusElement.textContent = message;
  statusElement.className = "status-message";
  if (type === "error") statusElement.classList.add("status-red");
  else if (type === "success") statusElement.classList.add("status-green");
  else if (type === "warning") statusElement.classList.add("status-orange");
}

/**
 * Sets the instructions HTML content in the UI.
 * @param {string} htmlContent - The HTML content to display in the instructions section.
 */
function setInstructions(htmlContent) {
  instructionsElement.innerHTML = htmlContent;
}

/**
 * Shows or hides the loading spinner.
 */
function showSpinner() {
  spinnerElement.style.display = "block";
}
function hideSpinner() {
  spinnerElement.style.display = "none";
}

/**
 * Shows specific buttons based on the arguments passed.
 *
 * Hides all buttons first, then shows the specified ones.
 * @param {...HTMLElement} buttons - The buttons to show (e.g., switchButton, continueButton).
 */
function showButtons(...buttons) {
  // Hide all relevant buttons first
  [switchButton, continueButton].forEach((btn) => (btn.style.display = "none"));
  // Then show the ones passed as arguments
  buttons.forEach((btn) => (btn.style.display = "block"));
}

// --- API Calls to Python Backend ---
/**
 * Fetches the active network details from the Python backend.
 *
 * @returns {Promise<Object>} - Returns an object with chainId, rpcUrl, and networkName.
 */
async function getBoaNetworkDetails() {
  try {
    const response = await fetch("/api/boa-network-details");
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    // Convert chainId to integer for comparison, keep others as strings
    boaNetworkDetails = {
      chainId: parseInt(data.chainId), // Convert to integer for comparison
      rpcUrl: data.rpcUrl,
      networkName: data.networkName,
    };
    return boaNetworkDetails;
  } catch (error) {
    // Log the error and set a user-friendly status message
    console.error("Error fetching Boa network details:", error);
    setStatus(
      "Error: Could not fetch Boa network details. Check backend server.",
      "error"
    );
    return null;
  }
}

/**
 * Reports the connected MetaMask account to the Python backend.
 *
 * @param {string} account - The connected MetaMask account address.
 */
async function reportConnectedAccount(account) {
  try {
    // Call Python backend to report the connected account
    await fetch("/report_connected_account", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account: account }),
    });
    console.log("Account reported to Python server.");
  } catch (error) {
    console.error("Error reporting account to Python:", error);
  }
}

/**
 * Signals the Python backend that the network is synced and ready.
 * This is called after network switch.
 */
async function signalPythonBackendNetworkSynced() {
  try {
    // Call Python backend to signal that the network is synced
    const response = await fetch("/api/network-synced", { method: "POST" });
    // Check if the response is OK (status 200)
    // If not, throw an error to be caught in the catch block
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    // If the response is OK, log success and update UI
    console.log("Signaled Python backend that network is synced.");
    // setStatus("Network synced! Script should now be continuing...", "success");
    // setInstructions("You can close this browser tab.");
    // showButtons(); // Hide all buttons
  } catch (error) {
    console.error("Failed to signal Python backend:", error);
    alert(
      "Failed to signal backend. Please check your script terminal for errors."
    );
  }
}

/**
 * Sends a heartbeat to the Python backend to check if it's still alive.
 *
 * If the heartbeat fails, it clears the polling and heartbeat intervals.
 */
async function sendHeartbeat() {
  try {
    // Send a heartbeat request to the Python server
    await fetch("/heartbeat", { method: "GET" });
  } catch (error) {
    console.error("Heartbeat failed, Python server might be down:", error);
    clearInterval(heartbeatInterval);
    setStatus("Connection to Moccasin CLI lost.", "error");
  }
}

// --- MetaMask Interaction Functions ---
/**
 * Gets the current chain ID from MetaMask.
 * @returns {Promise<number|null>} - Returns the chain ID as an integer, or null if MetaMask is not available.
 */
async function getMetaMaskChainId() {
  if (typeof window.ethereum === "undefined") return null;
  try {
    // Request the chain ID from MetaMask
    // This returns a hex string, e.g., '0x1' for Ethereum mainnet
    const chainIdHex = await window.ethereum.request({ method: "eth_chainId" });
    return parseInt(chainIdHex, 16); // Convert hex string to integer
  } catch (error) {
    console.error("Error getting MetaMask chainId:", error);
    return null;
  }
}

/**
 * Handles the network switch request to MetaMask on event.
 *
 * If the network is not found, it provides instructions to add it manually.
 * @dev auto add function is not implemented but can be added later if needed.
 * @returns {Promise<void>}
 */
async function handleNetworkSwitch() {
  if (!window.ethereum || !boaNetworkDetails.chainId) return;

  // Convert the chain ID to hex format for MetaMask
  const targetChainIdHex = "0x" + boaNetworkDetails.chainId.toString(16);

  try {
    // Check if the current chain ID matches the target chain ID
    showSpinner();
    setStatus("Requesting MetaMask to switch network...", "default");
    await window.ethereum.request({
      method: "wallet_switchEthereumChain",
      params: [{ chainId: targetChainIdHex }],
    });
    // If successful, MetaMask will trigger 'chainChanged' event, which calls updateUI().
  } catch (switchError) {
    // Handle specific errors based on MetaMask's error codes
    hideSpinner();
    console.error("Error switching network:", switchError);
    // 4001: User rejected the request
    if (switchError.code === 4001) {
      setStatus("Network switch rejected by user.", "error");
      // 4902: User tried to switch to a network not added in MetaMask
    } else if (switchError.code === 4902) {
      // Network not found in MetaMask, instruct user to add manually
      setStatus("Network not found in MetaMask.", "warning");
      setInstructions(`
                <p>The network <strong>${boaNetworkDetails.networkName}</strong> (Chain ID: <strong>${boaNetworkDetails.chainId}</strong>) is not configured in your MetaMask.</p>
                <p>Please add it manually to MetaMask using the details below, then click 'Continue Script'.</p>
                <div class="code">
                <strong>Network Name:</strong> ${boaNetworkDetails.networkName}<br>
                <strong>RPC URL:</strong> ${boaNetworkDetails.rpcUrl}<br>
                <strong>Chain ID:</strong> ${boaNetworkDetails.chainId}<br>
                <strong>Currency Symbol:</strong> ETH (or equivalent)
                </div>
                `);
      showButtons(continueButton); // Only show continue button after manual instruction
      // -32002: Request already pending (MetaMask is already processing a request)
    } else if (switchError.code === -32002) {
      setStatus(
        "MetaMask request already pending. Please approve or reject the current request in MetaMask.",
        "warning"
      );
    } else {
      setStatus(
        `Error switching network: ${switchError.message || switchError.code
        }. Please try manually.`,
        "error"
      );
    }
  }
}

/**
 * Connects to MetaMask and retrieves the current account.
 *
 * If successful, it updates the global state and reports the account to the Python backend.
 * @returns {Promise<boolean>} - Returns true if connected, false otherwise.
 */
async function connectMetaMaskAndReportAccount() {
  if (typeof window.ethereum === "undefined") return false;
  try {
    // Request accounts from MetaMask
    const accounts = await window.ethereum.request({
      method: "eth_requestAccounts",
    });
    if (accounts.length > 0) {
      // Take the first account as the current account
      currentAccount = accounts[0];
      isMetaMaskConnected = true;
      reportConnectedAccount(currentAccount);
      return true;
    } else {
      // No accounts found, update UI accordingly
      setStatus(
        "No accounts found in MetaMask. Please connect an account.",
        "error"
      );
      return false;
    }
  } catch (error) {
    if (error.code === 4001) {
      setStatus("MetaMask connection rejected by user.", "error");
    } else {
      setStatus(`MetaMask connection error: ${error.message}`, "error");
    }
    return false;
  }
}

// --- Main UI Update Logic ---
/**
 * Updates the UI based on the current MetaMask connection status and network details.
 *
 * Checks if MetaMask is connected, if the network matches the Boa script requirements,
 * and shows appropriate buttons for switching networks or continuing the script.
 */
async function updateUI() {
  hideSpinner();
  // Get the current MetaMask chain ID and Boa network details
  const boaNetDetails = await getBoaNetworkDetails();
  if (!boaNetDetails) return;
  const metamaskChainId = await getMetaMaskChainId();

  showButtons(); // Hide all buttons by default

  if (metamaskChainId === null) {
    // MetaMask is not detected or not connected
    setStatus(
      "MetaMask not detected or not connected. Please install/unlock MetaMask extension.",
      "error"
    );
    setInstructions(
      "<p>Ensure your MetaMask extension is installed, unlocked, and click 'Connect' if prompted.</p>"
    );
    return;
  }

  if (metamaskChainId === null) {
    setStatus(
      "MetaMask not detected or not connected. Please install/unlock MetaMask extension.",
      "error"
    );
    setInstructions(
      "<p>Ensure your MetaMask extension is installed, unlocked, and click 'Connect' if prompted.</p>"
    );
    return;
  }

  if (boaNetDetails.chainId === metamaskChainId) {
    // Network matches, proceed with the script
    setStatus(
      `MetaMask is connected to the correct network! (Chain ID: ${metamaskChainId})`,
      "success"
    );
    setInstructions("<p>Checking account balance...</p>");
    await signalPythonBackendNetworkSynced();

    if (!isMetaMaskConnected) {
      // If MetaMask is not connected, prompt user to connect
      const connected = await connectMetaMaskAndReportAccount();
      if (connected) {
        // If connection is successful, start polling and heartbeat
        startHeartbeat();
        startAccountStatusPolling();
      } else {
        // If connection failed, update UI to prompt user
        setStatus(
          "MetaMask account not connected. Please connect your account.",
          "error"
        );
        setInstructions(
          "<p>Your network is correct, but an account is not connected. Click 'Connect' in MetaMask.</p>"
        );
        showButtons(); // No network buttons, but prompt for account
      }
    } else {
      // If MetaMask is already connected, just start polling and heartbeat
      startHeartbeat();
      startAccountStatusPolling();
    }
  } else {
    // Network mismatch, prompt user to switch networks
    setStatus(`NETWORK MISMATCH!`, "error");
    setInstructions(`
            <p>Your Boa script expects Chain ID: <strong>${boaNetDetails.chainId}</strong> (<strong>${boaNetDetails.networkName}</strong>).</p>
            <p>Your MetaMask is currently on Chain ID: <strong>${metamaskChainId}</strong>.</p>
            <p>Click 'Switch Network' below to try and switch. If the network is not found, you will be prompted to add it manually.</p>
            <div class="code">
                <strong>Network Name:</strong> ${boaNetDetails.networkName}<br>
                <strong>RPC URL:</strong> ${boaNetDetails.rpcUrl}<br>
                <strong>Chain ID:</strong> ${boaNetDetails.chainId}<br>
                <strong>Currency Symbol:</strong> ETH (or equivalent)
            </div>
        `);
    showButtons(switchButton); // Only show the "Switch Network" button
  }
}

// --- Transaction Polling and Reporting (Existing Logic) ---
/**
 * Fetches a pending transaction from the Python backend and processes it.
 *
 * If a transaction is found, it sends it to MetaMask for confirmation.
 * If no transaction is found, it does nothing (status 204).
 */
async function fetchAndProcessTransaction() {
  if (!isMetaMaskConnected || !currentAccount) {
    return;
  }

  try {
    // Fetch the pending transaction from the Python backend
    const response = await fetch("/get_pending_transaction");

    if (response.status === 200) {
      // If a transaction is found, parse the JSON response
      const txParams = await response.json();
      console.log("Received transaction request:", txParams);
      setStatus("Please confirm transaction in MetaMask...", "default");
      showSpinner();

      try {
        // Ensure the 'from' address matches the current MetaMask account
        if (
          txParams.from &&
          txParams.from.toLowerCase() !== currentAccount.toLowerCase()
        ) {
          console.warn(
            `Transaction 'from' address mismatch. Overwriting with connected account: ${currentAccount}`
          );
          txParams.from = currentAccount;
        }

        // Send the transaction to MetaMask
        const txHash = await window.ethereum.request({
          method: "eth_sendTransaction",
          params: [txParams],
        });

        // Log the transaction hash and update status
        console.log("Transaction sent. Hash: " + txHash);
        setStatus(
          `Transaction sent. Hash: ${txHash}. Waiting for receipt...`,
          "default"
        );

        // Poll for the transaction receipt
        const receipt = await pollForReceipt(txHash);
        const contractAddress = receipt ? receipt.contractAddress : null;

        // Log the successful transaction receipt
        reportTransactionResult({
          status: "success",
          hash: txHash,
          contractAddress: contractAddress,
          receipt: receipt,
        });
        setStatus("Transaction confirmed and processed.", "success");
      } catch (txError) {
        // Handle transaction errors
        console.error("MetaMask transaction error:", txError);
        if (txError.code === 4001) {
          setStatus("Transaction rejected by user.", "error");
        } else if (txError.code === -32603) {
          setStatus(
            `Transaction error: ${txError.message}. Check gas limit or funds.`,
            "error"
          );
        } else {
          setStatus(`Transaction failed: ${txError.message}`, "error");
        }
        // Report the error to the Python backend
        reportTransactionResult({
          status: "error",
          error: txError.message,
          code: txError.code,
        });
      } finally {
        hideSpinner();
      }
    } else if (response.status === 204) {
      // No pending transaction - keep quiet
    } else {
      console.error("Error fetching transaction:", response.status);
      setStatus(`Error from CLI: ${response.status}`, "error");
    }
  } catch (error) {
    // Handle network errors or other issues
    console.error("Network error during transaction fetch:", error);
    setStatus("Lost connection to Moccasin CLI.", "error");
    clearInterval(heartbeatInterval);
    clearInterval(pollingInterval);
  }
}

/**
 * Polls for the transaction receipt using the transaction hash.
 *
 * Retries up to maxAttempts with a delay between attempts.
 * If the transaction is not found or reverts, it throws an error.
 * This function is useful for waiting for the transaction to be mined and confirmed.
 *
 * @param {string} txHash - The transaction hash to poll for.
 * @param {number} maxAttempts - Maximum number of attempts to poll for the receipt.
 * @param {number} delay - Delay in milliseconds between attempts.
 * @returns {Promise<Object>} - Returns the transaction receipt if found.
 * @throws {Error} - Throws an error if the transaction is not found or if it reverts.
 */
async function pollForReceipt(txHash, maxAttempts = 60, delay = 5000) {
  let attempts = 0;
  // Start polling for the transaction receipt
  while (attempts < maxAttempts) {
    try {
      // Attempt to get the transaction receipt from MetaMask
      const receipt = await window.ethereum.request({
        method: "eth_getTransactionReceipt",
        params: [txHash],
      });
      if (receipt) {
        // If receipt is found, check its status
        if (receipt.status === "0x0") {
          throw new Error(`Transaction reverted on chain: ${txHash}`);
        }
        return receipt;
      }
    } catch (error) {
      // If receipt is not found, it may still be pending
      console.warn(
        `Error getting receipt for ${txHash} (attempt ${attempts + 1
        }/${maxAttempts}): ${error.message}`
      );
    }
    // Increment attempts and wait before retrying
    attempts++;
    await new Promise((resolve) => setTimeout(resolve, delay));
  }
  // If we reach here, it means we exhausted all attempts without finding the receipt
  throw new Error(`Timeout waiting for transaction receipt: ${txHash}`);
}

/**
 * Reports the transaction result to the Python backend.
 *
 * This function is called after a transaction is processed, whether successful or failed.
 * It sends the transaction hash, status, and any error details to the Python server.
 *
 * @param {Object} result - The result object containing transaction details.
 */
async function reportTransactionResult(result) {
  try {
    // Call Python backend to report the transaction result
    await fetch("/report_transaction_result", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(result),
    });
    console.log("Transaction result reported to Python server.");
  } catch (error) {
    console.error("Error reporting transaction result to Python:", error);
  }
}

// --- Event Listeners and Initial Setup ---
window.ethereum.on("accountsChanged", (accounts) => {
  // Handle account changes in MetaMask
  if (accounts.length === 0) {
    // If no accounts are available, reset the current account and UI
    currentAccount = null;
    isMetaMaskConnected = false;
    reportConnectedAccount(null);
    clearInterval(pollingInterval);
    pollingInterval = null;
    heartbeatInterval = null;
    updateUI();
  } else {
    // If accounts are available, update the current account
    currentAccount = accounts[0];
    isMetaMaskConnected = true;
    reportConnectedAccount(currentAccount);
    updateUI();
    if (accountStatusInterval) {
      checkAndHandleAccountStatus();
    }
  }
});

window.ethereum.on("chainChanged", (chainId) => {
  // Handle chain changes in MetaMask
  console.log(`MetaMask chain changed to ${chainId}.`);
  updateUI();
});

window.ethereum.on("disconnect", (error) => {
  // Handle MetaMask disconnection
  // Reset the current account and UI state
  console.error("MetaMask disconnected:", error);
  currentAccount = null;
  isMetaMaskConnected = false;
  reportConnectedAccount(null);
  clearInterval(pollingInterval);
  clearInterval(heartbeatInterval);
  pollingInterval = null;
  heartbeatInterval = null;
  updateUI();
});

// Initialize the UI when the document is ready
document.addEventListener("DOMContentLoaded", () => {
  // Attach button event listeners
  switchButton.addEventListener("click", handleNetworkSwitch);
  continueButton.addEventListener("click", signalPythonBackendNetworkSynced);

  updateUI();
});

/**
 * Starts the transaction polling interval if not already started.
 *
 * This function is called after MetaMask is connected and the network is verified.
 */
function startTransactionPolling() {
  if (!pollingInterval) {
    pollingInterval = setInterval(fetchAndProcessTransaction, 1000);
    console.log("Started transaction polling.");
  }
}

/**
 * Starts the heartbeat interval to keep the connection alive with the Python backend.
 *
 * This function is called after MetaMask is connected and the network is verified.
 */
function startHeartbeat() {
  if (!heartbeatInterval) {
    heartbeatInterval = setInterval(
      sendHeartbeat,
      HEARTBEAT_INTERVAL_CLIENT_MS
    );
  }
}

/**
 * Starts polling for account status when we need to check for balance issues
 */
function startAccountStatusPolling() {
  if (!accountStatusInterval) {
    // Check immediately
    checkAndHandleAccountStatus();

    // Then check every 2 seconds
    accountStatusInterval = setInterval(checkAndHandleAccountStatus, 2000);
  }
}

/**
 * Stops the account status polling
 */
function stopAccountStatusPolling() {
  if (accountStatusInterval) {
    clearInterval(accountStatusInterval);
    accountStatusInterval = null;
  }
}

/**
 * Checks account status and updates UI if there's an issue
 */
async function checkAndHandleAccountStatus() {
  try {
    const accountStatus = await checkAccountStatus();
    if (!accountStatus.ok && accountStatus.error === 'zero_balance') {
      // Show zero balance warning
      setStatus("Connected wallet has 0 gas!", "error");
      setInstructions(`
                <p>The account <strong>${accountStatus.current_address}</strong> has <strong>zero balance</strong>.</p>
                <p>Please connect to an account with funds in MetaMask.</p>
            `);
      showButtons(); // Hide all buttons while waiting
    } else if (accountStatus.ok) {
      // Account is good, stop polling for account status
      stopAccountStatusPolling();
      setStatus("Account connected successfully!", "success");
      setInstructions("<p>Account has balance. Waiting for transactions from your script...</p>");
      showButtons(); // Hide buttons - transactions will come automatically
      startTransactionPolling();
    }
  } catch (error) {
    console.error("Error checking account status:", error);
  }
}


/**
 * Checks the account status from the Python backend.
 * @returns {Promise<Object>} - Returns the account status object.
 */
async function checkAccountStatus() {
  try {
    const response = await fetch("/check_account_status");
    return await response.json();
  } catch (error) {
    console.error("Error checking account status:", error);
    return { ok: false }; // Default to OK if we can't check
  }
}