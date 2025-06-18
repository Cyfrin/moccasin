// The main application entry point and orchestrator.

import { setStatus, setInstructions, hideSpinner } from "./ui.js";
import * as api from "./api.js";
import * as metamask from "./metamask.js";
import * as polling from "./polling.js";
import { state } from "./state.js"; // Access and modify global state

/**
 * Performs a complete application disconnect and cleanup.
 * This function handles stopping all intervals, clearing UI, and revoking MetaMask permissions.
 */
async function disconnectApp() {
  console.log("Initiating full application disconnect...");
  // Set flag to ensure disconnect state is handled properly
  state.isDisconnecting = true;
  polling.stopAllIntervals(); // Stop all background tasks

  // Clean up state
  state.currentAccount = null;
  state.isMetaMaskConnected = false;
  state.boaNetworkDetails = {};

  // Report disconnect to backend using the unified status reporter
  // Use reportAccountConnectionStatus
  await api.reportAccountConnectionStatus(null, "disconnected");

  // Attempt to revoke MetaMask permissions
  await metamask.revokeMetaMaskPermissions();

  // Update UI to reflect disconnected state
  setInstructions(
    "<p>You have been disconnected from the DApp. You can now close this tab.</p>"
  );
  setStatus("Application disconnected.");
  // Reset disconnect flag
  state.isDisconnecting = false;
}

/**
 * Updates the UI and overall application state based on MetaMask and backend status.
 * This is the central logic loop after initial load and on key events.
 */
async function updateUI() {
  if (state.isDisconnecting) {
    // Immediately exit if disconnecting
    console.warn("updateUI() skipped because disconnectApp() is in progress.");
    return;
  }

  // Hide any previous spinner and reset UI
  hideSpinner();

  // Always ensure heartbeat and disconnect polling are running
  // @dev These are fundamental for maintaining communication with the Python backend
  //  and receiving explicit shutdown signals.
  polling.startHeartbeatPolling();
  polling.startDisconnectPolling();

  // 1. Check MetaMask availability
  if (!metamask.isMetaMaskAvailable()) {
    setStatus(
      "MetaMask not detected or not connected. Please install/unlock MetaMask extension.",
      "error"
    );
    setInstructions(
      "<p>Ensure your MetaMask extension is installed, unlocked, and click 'Connect' if prompted.</p>"
    );
    polling.stopAccountStatusPolling();
    polling.stopMessageSigningPolling();
    polling.stopTransactionPolling();
    return;
  }

  // 2. Fetch Boa Network Details
  const boaDetailsFetched = await api.getBoaNetworkDetails();
  if (!boaDetailsFetched) {
    // Stop specific polling, but keep heartbeat/disconnect
    polling.stopAccountStatusPolling();
    polling.stopMessageSigningPolling();
    polling.stopTransactionPolling();
    return;
  }

  // 3. Get MetaMask Chain ID
  const metamaskChainId = await metamask.getMetaMaskChainId();
  if (metamaskChainId === null) {
    // MetaMask might be available but not providing chainId, or temporarily offline
    setStatus("MetaMask connection issue. Cannot get chain ID.", "error");
    setInstructions(
      "<p>Please ensure MetaMask is unlocked and connected to a network.</p>"
    );
    // Stop specific polling, but keep heartbeat/disconnect
    polling.stopAccountStatusPolling();
    polling.stopMessageSigningPolling();
    polling.stopTransactionPolling();
    return;
  }

  // 4. Compare Network IDs
  if (state.boaNetworkDetails.chainId === metamaskChainId) {
    // Network matches!
    setStatus(
      `MetaMask is connected to the correct network! (Chain ID: ${metamaskChainId})`,
      "success"
    );

    // Signal Python backend that network is synced (important after switch)
    const networkSynced = await api.signalPythonBackendNetworkSynced();
    if (!networkSynced) {
      // If backend can't be signaled, it's a critical error, disconnect
      disconnectApp();
      return;
    }

    // If not already connected or account is null, try to connect accounts
    if (!state.isMetaMaskConnected || !state.currentAccount) {
      setStatus("Attempting to connect MetaMask account...", "info");
      const connected = await metamask.requestMetaMaskAccounts();
      if (connected) {
        setStatus(
          "Account connected successfully! Checking balance...",
          "info"
        );
        // Start account status polling, which will then start transaction polling
        polling.startAccountStatusPolling();
      } else {
        // If connection failed (e.g., user rejected)
        setStatus("MetaMask account not connected or rejected.", "error");
        setInstructions(
          "<p>You rejected the connection or no accounts are available.</p>"
        );
      }
    } else {
      // Already connected to correct network and account, start polling if not already
      setStatus(
        "Account connected and network synced. Waiting for transactions...",
        "success"
      );
      setInstructions(
        "<p>Your script should now be sending transactions. Please keep this tab open.</p>"
      );
      // Ensure specific polling is active if it's not already
      polling.startAccountStatusPolling();
    }
  } else {
    // Network mismatch, prompt user to switch networks
    setStatus(`NETWORK MISMATCH!`, "error");
    setInstructions(`
            <p>Your Boa script expects Chain ID: <strong>${state.boaNetworkDetails.chainId}</strong> (<strong>${state.boaNetworkDetails.networkName}</strong>).</p>
            <p>Your MetaMask is currently on Chain ID: <strong>${metamaskChainId}</strong>.</p>
            <strong>Please switch to the correct network in MetaMask.</strong>
            <p>If the network is not available, you can add it manually using the details below:</p>
            <div class="code">
                <strong>Network Name:</strong> ${state.boaNetworkDetails.networkName}<br>
                <strong>RPC URL:</strong> ${state.boaNetworkDetails.rpcUrl}<br>
                <strong>Chain ID:</strong> ${state.boaNetworkDetails.chainId}<br>
                <strong>Currency Symbol:</strong> ETH (or equivalent)
            </div>
        `);
    // Stop specific polling, but keep heartbeat/disconnect
    polling.stopAccountStatusPolling();
    polling.stopMessageSigningPolling();
    polling.stopTransactionPolling();
  }
}

// --- Event Listeners ---

// Set the callback for intervals to trigger a full app disconnect
polling.setOnAppDisconnectCallback(disconnectApp);

window.ethereum.on("accountsChanged", async (accounts) => {
  console.log("MetaMask accountsChanged event received:", accounts);
  if (state.isDisconnecting) {
    // If we're already disconnecting, skip handling accountsChanged
    console.warn(
      "accountsChanged handler skipped because disconnectApp() is in progress."
    );
    return;
  }
  if (accounts.length === 0) {
    setStatus(
      "MetaMask account disconnected. Please re-connect if needed.",
      "warning"
    );
    // If we were previously connected, trigger a full app disconnect
    if (state.isMetaMaskConnected) {
      await disconnectApp(); // This will now use reportAccountConnectionStatus
    } else {
      // If we weren't connected, just reset state internally without full disconnect call
      state.currentAccount = null;
      state.isMetaMaskConnected = false;
      // Use reportAccountConnectionStatus for null account
      await api.reportAccountConnectionStatus(null, "disconnected");
      updateUI(); // Re-evaluate UI state
    }
  } else {
    // An account is connected or changed.
    const newAccount = accounts[0];
    // Check if the primary account has actually changed (case-insensitive)
    if (
      newAccount.toLowerCase() !==
      (state.currentAccount ? state.currentAccount.toLowerCase() : "")
    ) {
      console.log(
        `Account changed from ${
          state.currentAccount || "none"
        } to ${newAccount}`
      );
      state.currentAccount = newAccount;
      state.isMetaMaskConnected = true; // Assume connected if accounts are present
      // Use reportAccountConnectionStatus for new account
      await api.reportAccountConnectionStatus(
        state.currentAccount,
        "connected"
      );
      updateUI(); // Re-evaluate network and account status, which will start intervals
    } else {
      console.log(
        "accountsChanged fired but primary account is the same. Re-verifying state."
      );
      // Account is the same, but ensure we're fully connected and polling
      if (
        !state.isMetaMaskConnected ||
        !polling.heartbeatInterval ||
        !polling.transactionPollingInterval
      ) {
        state.currentAccount = newAccount; // Ensure currentAccount is set
        state.isMetaMaskConnected = true;
        // Use reportAccountConnectionStatus for existing account
        await api.reportAccountConnectionStatus(
          state.currentAccount,
          "connected"
        );
        updateUI();
      }
    }
  }
});

window.ethereum.on("chainChanged", (chainId) => {
  console.log(`MetaMask chain changed to ${chainId}.`);
  updateUI(); // Re-evaluate UI when chain changes
});

window.ethereum.on("disconnect", (error) => {
  console.error("MetaMask provider disconnected:", error);
  setStatus(`MetaMask provider disconnected: ${error.message}.`, "error");
  disconnectApp(); // Full disconnect procedure if provider disconnects
});

// Listener for when the browser tab is closing
window.addEventListener("beforeunload", async (event) => {
  if (state.currentAccount) {
    try {
      // Use sendBeacon for reliable, non-blocking send on page close
      // This part is fine as /browser_closing handler exists and handles it.
      navigator.sendBeacon(
        "/browser_closing",
        JSON.stringify({ account: state.currentAccount, action: "disconnect" })
      );
      console.log("Signal sent to backend: browser closing.");

      // Attempt to revoke permissions on unload - browser might block this
      metamask
        .revokeMetaMaskPermissions()
        .catch((e) =>
          console.warn("Error revoking MetaMask permissions on unload:", e)
        );
    } catch (e) {
      console.warn(
        "Error sending browser closing signal or attempting MetaMask disconnect on unload:",
        e
      );
    }
  }
  polling.stopAllIntervals(); // Ensure all intervals are cleared immediately
});

// Initial setup on DOMContentLoaded
document.addEventListener("DOMContentLoaded", () => {
  updateUI(); // Initial UI update and MetaMask checks
});
