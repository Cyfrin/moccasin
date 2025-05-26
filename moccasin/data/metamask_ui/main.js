// moccasin/data/metamask_ui/main.js

const HEARTBEAT_INTERVAL_CLIENT_MS = 5000;

const statusElement = document.getElementById('status-message');
const instructionsElement = document.getElementById('instructions');
const switchButton = document.getElementById('switchNetworkButton');
// const addButton = document.getElementById('addNetworkButton'); // Removed as per user request
const continueButton = document.getElementById('continueButton');
const spinnerElement = document.querySelector('.loading-spinner');

let currentAccount = null;
let isMetaMaskConnected = false;
let heartbeatInterval = null;
let pollingInterval = null;
let boaNetworkDetails = {};

// --- Utility Functions for UI Updates ---
function setStatus(message, type = 'default') {
    statusElement.textContent = message;
    statusElement.className = 'status-message';
    if (type === 'error') statusElement.classList.add('status-red');
    else if (type === 'success') statusElement.classList.add('status-green');
    else if (type === 'warning') statusElement.classList.add('status-orange');
}

function setInstructions(htmlContent) {
    instructionsElement.innerHTML = htmlContent;
}

function showSpinner() { spinnerElement.style.display = 'block'; }
function hideSpinner() { spinnerElement.style.display = 'none'; }

function showButtons(...buttons) {
    // Hide all relevant buttons first
    [switchButton, continueButton].forEach(btn => btn.style.display = 'none');
    // Then show the ones passed as arguments
    buttons.forEach(btn => btn.style.display = 'block');
}

// --- API Calls to Python Backend ---
async function getBoaNetworkDetails() {
    try {
        const response = await fetch('/api/boa-network-details');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        // Convert chainId to integer for comparison, keep others as strings
        boaNetworkDetails = {
            chainId: parseInt(data.chainId), // Convert to integer for comparison
            rpcUrl: data.rpcUrl,
            networkName: data.networkName
        };
        return boaNetworkDetails;
    } catch (error) {
        console.error("Error fetching Boa network details:", error);
        setStatus("Error: Could not fetch Boa network details. Check backend server.", 'error');
        return null;
    }
}

async function reportConnectedAccount(account) {
    try {
        await fetch('/report_connected_account', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ account: account })
        });
        console.log('Account reported to Python server.');
    } catch (error) {
        console.error('Error reporting account to Python:', error);
    }
}

async function signalPythonBackendNetworkSynced() {
    try {
        const response = await fetch('/api/network-synced', { method: 'POST' });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        console.log("Signaled Python backend that network is synced.");
        setStatus("Network synced! Script should now be continuing...", 'success');
        setInstructions("You can close this browser tab.");
        showButtons(); // Hide all buttons
    } catch (error) {
        console.error("Failed to signal Python backend:", error);
        alert('Failed to signal backend. Please check your script terminal for errors.');
    }
}

async function sendHeartbeat() {
    try {
        await fetch('/heartbeat', { method: 'GET' });
    } catch (error) {
        console.error('Heartbeat failed, Python server might be down:', error);
        clearInterval(heartbeatInterval);
        setStatus('Connection to Moccasin CLI lost.', 'error');
    }
}

// --- MetaMask Interaction Functions ---
async function getMetaMaskChainId() {
    if (typeof window.ethereum === 'undefined') return null;
    try {
        const chainIdHex = await window.ethereum.request({ method: 'eth_chainId' });
        return parseInt(chainIdHex, 16); // Convert hex string to integer
    } catch (error) {
        console.error("Error getting MetaMask chainId:", error);
        return null;
    }
}

/**
 * Attempts to switch to the target network. If the network is not found (error 4902),
 * it instructs the user to add it manually.
 */
async function handleNetworkSwitch() {
    if (!window.ethereum || !boaNetworkDetails.chainId) return;

    const targetChainIdHex = '0x' + boaNetworkDetails.chainId.toString(16); 
    
    try {
        showSpinner();
        setStatus("Requesting MetaMask to switch network...", 'default');
        await window.ethereum.request({
            method: 'wallet_switchEthereumChain',
            params: [{ chainId: targetChainIdHex }],
        });
        // If successful, MetaMask will trigger 'chainChanged' event, which calls updateUI().
    } catch (switchError) {
        hideSpinner();
        console.error("Error switching network:", switchError);
        if (switchError.code === 4001) {
            setStatus('Network switch rejected by user.', 'error');
        } else if (switchError.code === 4902) {
            // Network not found in MetaMask, instruct user to add manually
            setStatus('Network not found in MetaMask.', 'warning');
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
            // DO NOT signal Python backend here, as user has a manual step
        } else if (switchError.code === -32002) {
            setStatus('MetaMask request already pending. Please approve or reject the current request in MetaMask.', 'warning');
        } else {
            setStatus(`Error switching network: ${switchError.message || switchError.code}. Please try manually.`, 'error');
        }
        // No need to call updateUI() here if we've provided specific instructions and buttons
        // The chainChanged event will trigger updateUI() if the user successfully switches/adds manually.
    }
}

// handleNetworkAdd function is removed as per user request.

async function connectMetaMaskAndReportAccount() {
    if (typeof window.ethereum === 'undefined') return false;
    try {
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        if (accounts.length > 0) {
            currentAccount = accounts[0];
            isMetaMaskConnected = true;
            reportConnectedAccount(currentAccount);
            return true;
        } else {
            setStatus("No accounts found in MetaMask. Please connect an account.", 'error');
            return false;
        }
    } catch (error) {
        if (error.code === 4001) {
            setStatus("MetaMask connection rejected by user.", 'error');
        } else {
            setStatus(`MetaMask connection error: ${error.message}`, 'error');
        }
        return false;
    }
}

// --- Main UI Update Logic ---
async function updateUI() {
    hideSpinner();
    const boaNetDetails = await getBoaNetworkDetails();
    if (!boaNetDetails) return;

    const metamaskChainId = await getMetaMaskChainId();

    showButtons(); // Hide all buttons by default
    
    if (metamaskChainId === null) {
        setStatus("MetaMask not detected or not connected. Please install/unlock MetaMask extension.", 'error');
        setInstructions("<p>Ensure your MetaMask extension is installed, unlocked, and click 'Connect' if prompted.</p>");
        return;
    }

    if (boaNetDetails.chainId === metamaskChainId) {
        setStatus(`MetaMask is connected to the correct network! (Chain ID: ${metamaskChainId})`, 'success');
        setInstructions("<p>Click 'Continue Script' below to proceed with your Boa script, or it may continue automatically.</p>");
        showButtons(continueButton);
        
        await signalPythonBackendNetworkSynced(); 

        if (!isMetaMaskConnected) {
             const connected = await connectMetaMaskAndReportAccount();
             if (connected) {
                 startTransactionPolling();
                 startHeartbeat();
             } else {
                 setStatus("MetaMask account not connected. Please connect your account.", 'error');
                 setInstructions("<p>Your network is correct, but an account is not connected. Click 'Connect' in MetaMask.</p>");
                 showButtons(); // No network buttons, but prompt for account
             }
        } else {
             startTransactionPolling();
             startHeartbeat();
        }

    } else {
        setStatus(`NETWORK MISMATCH!`, 'error');
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
async function fetchAndProcessTransaction() {
    if (!isMetaMaskConnected || !currentAccount) {
        return;
    }
    
    try {
        const response = await fetch('/get_pending_transaction');

        if (response.status === 200) {
            const txParams = await response.json();
            console.log('Received transaction request:', txParams);
            setStatus("Please confirm transaction in MetaMask...", 'default');
            showSpinner();

            try {
                if (txParams.from && txParams.from.toLowerCase() !== currentAccount.toLowerCase()) {
                    console.warn(`Transaction 'from' address mismatch. Overwriting with connected account: ${currentAccount}`);
                    txParams.from = currentAccount;
                }
                
                const txHash = await window.ethereum.request({
                    method: 'eth_sendTransaction',
                    params: [txParams],
                });

                console.log('Transaction sent. Hash: ' + txHash);
                setStatus(`Transaction sent. Hash: ${txHash}. Waiting for receipt...`, 'default');

                const receipt = await pollForReceipt(txHash);
                const contractAddress = receipt ? receipt.contractAddress : null;

                reportTransactionResult({
                    status: 'success',
                    hash: txHash,
                    contractAddress: contractAddress,
                    receipt: receipt 
                });
                setStatus("Transaction confirmed and processed.", 'success');

            } catch (txError) {
                console.error('MetaMask transaction error:', txError);
                if (txError.code === 4001) {
                    setStatus("Transaction rejected by user.", 'error');
                } else if (txError.code === -32603) {
                    setStatus(`Transaction error: ${txError.message}. Check gas limit or funds.`, 'error');
                } else {
                    setStatus(`Transaction failed: ${txError.message}`, 'error');
                }
                reportTransactionResult({
                    status: 'error',
                    error: txError.message,
                    code: txError.code,
                });
            } finally {
                hideSpinner();
            }
        } else if (response.status === 204) {
            // No pending transaction - keep quiet
        } else {
            console.error('Error fetching transaction:', response.status);
            setStatus(`Error from CLI: ${response.status}`, 'error');
        }
    } catch (error) {
        console.error('Network error during transaction fetch:', error);
        setStatus('Lost connection to Moccasin CLI.', 'error');
        clearInterval(heartbeatInterval);
        clearInterval(pollingInterval);
    }
}

async function pollForReceipt(txHash, maxAttempts = 60, delay = 5000) {
    let attempts = 0;
    while (attempts < maxAttempts) {
        try {
            const receipt = await window.ethereum.request({
                method: 'eth_getTransactionReceipt',
                params: [txHash],
            });
            if (receipt) {
                if (receipt.status === '0x0') {
                    throw new Error(`Transaction reverted on chain: ${txHash}`);
                }
                return receipt;
            }
        } catch (error) {
            console.warn(`Error getting receipt for ${txHash} (attempt ${attempts + 1}/${maxAttempts}): ${error.message}`);
        }
        attempts++;
        await new Promise(resolve => setTimeout(resolve, delay));
    }
    throw new Error(`Timeout waiting for transaction receipt: ${txHash}`);
}


async function reportTransactionResult(result) {
    try {
        await fetch('/report_transaction_result', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(result)
        });
        console.log('Transaction result reported to Python server.');
    } catch (error) {
        console.error('Error reporting transaction result to Python:', error);
    }
}


// --- Event Listeners and Initial Setup ---
window.ethereum.on('accountsChanged', (accounts) => {
    if (accounts.length === 0) {
        currentAccount = null;
        isMetaMaskConnected = false;
        reportConnectedAccount(null);
        clearInterval(pollingInterval);
        clearInterval(heartbeatInterval);
        pollingInterval = null;
        heartbeatInterval = null;
        updateUI();
    } else {
        currentAccount = accounts[0];
        isMetaMaskConnected = true;
        reportConnectedAccount(currentAccount);
        updateUI();
    }
});

window.ethereum.on('chainChanged', (chainId) => {
    console.log(`MetaMask chain changed to ${chainId}.`);
    updateUI();
});

window.ethereum.on('disconnect', (error) => {
    console.error('MetaMask disconnected:', error);
    currentAccount = null;
    isMetaMaskConnected = false;
    reportConnectedAccount(null);
    clearInterval(pollingInterval);
    clearInterval(heartbeatInterval);
    pollingInterval = null;
    heartbeatInterval = null;
    updateUI();
});

document.addEventListener('DOMContentLoaded', () => {
    // Attach button event listeners
    switchButton.addEventListener('click', handleNetworkSwitch);
    continueButton.addEventListener('click', signalPythonBackendNetworkSynced);

    updateUI();
});

// Functions to start intervals
function startTransactionPolling() {
    if (!pollingInterval) {
        pollingInterval = setInterval(fetchAndProcessTransaction, 1000);
        console.log('Started transaction polling.');
    }
}

function startHeartbeat() {
    if (!heartbeatInterval) {
        heartbeatInterval = setInterval(sendHeartbeat, HEARTBEAT_INTERVAL_CLIENT_MS);
    }
}
