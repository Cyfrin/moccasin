// moccasin/data/metamask_ui/main.js

const HEARTBEAT_INTERVAL_CLIENT_MS = 5000; // Match Python's setting

const statusElement = document.getElementById('account-status');
const spinnerElement = document.querySelector('.loading-spinner');

let currentAccount = null;
let isMetaMaskConnected = false;
let heartbeatInterval = null;

function updateStatus(message, isError = false) {
    statusElement.textContent = message;
    statusElement.className = isError ? 'error' : '';
    if (isError) {
        spinnerElement.style.display = 'none';
    }
}

async function connectMetaMask() {
    if (typeof window.ethereum === 'undefined') {
        updateStatus("MetaMask not detected! Please install MetaMask to proceed.", true);
        return false;
    }

    try {
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        if (accounts.length > 0) {
            currentAccount = accounts[0];
            isMetaMaskConnected = true;
            updateStatus(`Account: ${currentAccount}`);
            reportConnectedAccount(currentAccount);
            startTransactionPolling();
            startHeartbeat();
            return true;
        } else {
            updateStatus("No accounts found in MetaMask. Please connect an account.", true);
            return false;
        }
    } catch (error) {
        if (error.code === 4001) {
            // User rejected connection
            updateStatus("MetaMask connection rejected by user.", true);
        } else {
            updateStatus(`MetaMask connection error: ${error.message}`, true);
        }
        return false;
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

async function sendHeartbeat() {
    try {
        await fetch('/heartbeat', { method: 'GET' });
        // console.log('Heartbeat sent.');
    } catch (error) {
        console.error('Heartbeat failed, Python server might be down:', error);
        clearInterval(heartbeatInterval);
        updateStatus('Connection to Moccasin CLI lost.', true);
        // Optionally, disable further operations or prompt user to restart CLI
    }
}

function startHeartbeat() {
    if (!heartbeatInterval) {
        heartbeatInterval = setInterval(sendHeartbeat, HEARTBEAT_INTERVAL_CLIENT_MS);
    }
}

async function fetchAndProcessTransaction() {
    if (!isMetaMaskConnected) return;

    try {
        const response = await fetch('/get_pending_transaction', { method: 'GET' });

        if (response.status === 200) {
            const txParams = await response.json();
            console.log('Received transaction request:', txParams);
            updateStatus("Please confirm transaction in MetaMask...", false);
            spinnerElement.style.display = 'block'; // Show spinner while waiting for confirmation

            try {
                // Ensure the 'from' address matches the connected account
                if (txParams.from && txParams.from.toLowerCase() !== currentAccount.toLowerCase()) {
                    console.warn(`Transaction 'from' address mismatch. Expected: ${currentAccount}, Got: ${txParams.from}. MetaMask will likely use the connected account.`);
                    // MetaMask generally ignores the 'from' if it's not the connected account
                    // We can choose to overwrite it here for consistency if needed, but MetaMask handles it
                    txParams.from = currentAccount;
                }
                
                // eth_sendTransaction params must be an array of objects
                const txHash = await window.ethereum.request({
                    method: 'eth_sendTransaction',
                    params: [txParams],
                });

                console.log('Transaction sent. Hash: ' + txHash);
                updateStatus(`Transaction sent. Hash: ${txHash}. Waiting for receipt...`, false);

                // Poll for receipt and get contract address for deployment
                const receipt = await pollForReceipt(txHash);
                const contractAddress = receipt ? receipt.contractAddress : null;

                reportTransactionResult({
                    status: 'success',
                    hash: txHash,
                    contractAddress: contractAddress, // Include contract address if deployment
                    receipt: receipt // Optionally send full receipt
                });
                updateStatus("Transaction confirmed and processed.", false);

            } catch (txError) {
                console.error('MetaMask transaction error:', txError);
                updateStatus(`Transaction failed: ${txError.message}`, true);
                reportTransactionResult({
                    status: 'error',
                    error: txError.message,
                    code: txError.code, // MetaMask error code
                });
            } finally {
                spinnerElement.style.display = 'none';
            }
        } else if (response.status === 204) {
            // No pending transaction
            // updateStatus("Waiting for transactions...", false); // Too chatty, keep quiet
        } else {
            console.error('Error fetching transaction:', response.status);
            updateStatus(`Error from CLI: ${response.status}`, true);
        }
    } catch (error) {
        console.error('Network error during transaction fetch:', error);
        // This usually means the Python server is down or unreachable
        updateStatus('Lost connection to Moccasin CLI.', true);
        clearInterval(heartbeatInterval);
        // No need to report to server, as connection is lost
    }
}

async function pollForReceipt(txHash, maxAttempts = 60, delay = 5000) { // Max 5 mins, 5 sec delay
    let attempts = 0;
    while (attempts < maxAttempts) {
        try {
            const receipt = await window.ethereum.request({
                method: 'eth_getTransactionReceipt',
                params: [txHash],
            });
            if (receipt) {
                console.log('Transaction receipt:', receipt);
                // Check if transaction status is '0x0' (reverted)
                if (receipt.status === '0x0') {
                    throw new Error(`Transaction reverted on chain: ${txHash}`);
                }
                return receipt;
            }
        } catch (error) {
            console.warn(`Error getting receipt for ${txHash} (attempt ${attempts + 1}/${maxAttempts}): ${error.message}`);
            // Don't throw here, keep retrying or fail after max attempts
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

let pollingInterval = null;
function startTransactionPolling() {
    if (!pollingInterval) {
        // Poll frequently for new transaction requests
        pollingInterval = setInterval(fetchAndProcessTransaction, 1000); // Poll every second
        console.log('Started transaction polling.');
    }
}

// Event listeners for MetaMask account changes and disconnections
window.ethereum.on('accountsChanged', (accounts) => {
    if (accounts.length === 0) {
        updateStatus("MetaMask account disconnected or changed. Please connect.", true);
        isMetaMaskConnected = false;
        currentAccount = null;
        reportConnectedAccount(null); // Report disconnection to Python
        clearInterval(pollingInterval);
        clearInterval(heartbeatInterval);
        spinnerElement.style.display = 'none';
    } else {
        currentAccount = accounts[0];
        isMetaMaskConnected = true;
        updateStatus(`Account changed to: ${currentAccount}`);
        reportConnectedAccount(currentAccount);
        startTransactionPolling();
        startHeartbeat();
    }
});

window.ethereum.on('chainChanged', (chainId) => {
    // Reload if chain changes, or handle chain ID change gracefully
    console.log(`Chain changed to ${chainId}. Reloading page...`);
    window.location.reload();
});

window.ethereum.on('disconnect', (error) => {
    console.error('MetaMask disconnected:', error);
    updateStatus(`MetaMask disconnected: ${error.message}`, true);
    isMetaMaskConnected = false;
    currentAccount = null;
    reportConnectedAccount(null); // Report disconnection to Python
    clearInterval(pollingInterval);
    clearInterval(heartbeatInterval);
    spinnerElement.style.display = 'none';
});


// Initial connection attempt when the page loads
document.addEventListener('DOMContentLoaded', connectMetaMask);

