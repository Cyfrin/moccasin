// main.js
// Script to programmatically connect to MetaMask, fetch transaction details,
// send a transaction, and signal status to the Python server.

// Get references to the HTML elements that will display messages
const statusMessage = document.getElementById('statusMessage');
const transactionDetails = document.getElementById('transactionDetails');
const consoleMessage = document.getElementById('consoleMessage');
const closeTabMessage = document.getElementById('closeTabMessage');
const metaMaskHelperMessage = document.getElementById('metaMaskHelperMessage'); // New helper message element

let metaMaskPromptTimer; // Variable to hold the timer ID for the helper message
let heartbeatIntervalId; // Variable to hold the heartbeat interval ID

// Constants for heartbeat mechanism (must match server's expectation)
const HEARTBEAT_INTERVAL_MS = 5000; // Send heartbeat every 5 seconds

/**
 * Sends a shutdown signal to the Python server with a given status.
 * Also clears the heartbeat interval.
 * @param {string} status - The status of the MetaMask connection attempt or transaction outcome.
 */
async function sendShutdownSignal(status) {
    // Clear the heartbeat interval as the server is expected to shut down
    if (heartbeatIntervalId) {
        clearInterval(heartbeatIntervalId);
        heartbeatIntervalId = null;
        console.log('Heartbeat stopped.');
    }

    try {
        // Make a POST request to the '/shutdown' endpoint on the Python server.
        const response = await fetch('/shutdown', {
            method: 'POST',
            headers: {
                'Content-Type': 'text/plain' // Indicate that the body is plain text
            },
            body: status // Send the status string as the request body
        });
        const text = await response.text(); // Read the response from the server
        console.log('Shutdown signal sent:', text);
    } catch (error) {
        console.error('Error sending shutdown signal:', error);
    }
}

/**
 * Sends a heartbeat signal to the Python server.
 */
async function sendHeartbeat() {
    try {
        await fetch('/heartbeat', { method: 'GET' }); // Simple GET request for heartbeat
        // console.log('Heartbeat sent.'); // Uncomment for verbose heartbeat logging
    } catch (error) {
        console.error('Error sending heartbeat:', error);
        // If heartbeat fails, it likely means the server is already down or unreachable.
        // We don't need to explicitly shut down here, as the server's monitor will handle it.
    }
}

/**
 * Main function to handle MetaMask connection and transaction.
 */
async function runMetaMaskProcess() {
    statusMessage.textContent = 'Checking for MetaMask...';
    closeTabMessage.textContent = 'The server will shut down automatically after the attempt.';


    // Check if MetaMask's ethereum object is available in the window
    if (typeof window.ethereum === 'undefined') {
        console.log('MetaMask is not installed. Please install MetaMask to use this application.');
        statusMessage.textContent = 'MetaMask is not installed.';
        consoleMessage.textContent = 'Please install MetaMask to use this application.';
        closeTabMessage.textContent = 'You can now close this tab.';
        closeTabMessage.style.display = 'block';
        await sendShutdownSignal('metamask_not_installed');
        return; // Exit if MetaMask is not found
    }

    console.log('MetaMask is installed!');
    statusMessage.textContent = 'MetaMask detected. Requesting connection...';

    let accounts;
    try {
        // Request account access from MetaMask.
        // This will trigger the MetaMask pop-up for user approval.
        accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        const account = accounts[0];
        console.log('Connected to MetaMask!');
        console.log('Account:', account);

        const chainId = await window.ethereum.request({ method: 'eth_chainId' });
        console.log('Chain ID:', chainId);

        statusMessage.textContent = 'Successfully connected to MetaMask!';
        consoleMessage.textContent = `Connected Account: ${account}\nChain ID: ${chainId}`;
        transactionDetails.textContent = 'Fetching transaction details from server...';

        // Start sending heartbeats once connected
        heartbeatIntervalId = setInterval(sendHeartbeat, HEARTBEAT_INTERVAL_MS);
        console.log(`Heartbeat started, sending every ${HEARTBEAT_INTERVAL_MS / 1000} seconds.`);

        // --- Step 2: Fetch transaction details from Python server ---
        const txResponse = await fetch('/transaction_details');
        if (!txResponse.ok) {
            throw new Error(`HTTP error! status: ${txResponse.status}`);
        }
        const txParams = await txResponse.json();
        // Add the 'from' address from the connected MetaMask account
        txParams.from = account;

        console.log('Transaction details received:', txParams);
        transactionDetails.textContent = `Preparing transaction to: ${txParams.to} with value ${parseInt(txParams.value, 16)} wei.`;
        statusMessage.textContent = 'Awaiting transaction confirmation in MetaMask...';

        // --- IMPORTANT: Added logging before sending transaction ---
        console.log('Current Chain ID:', chainId); // Log chain ID
        console.log('Attempting to send transaction with parameters:', txParams);

        // Set a timer to display the helper message if the MetaMask pop-up doesn't appear promptly
        metaMaskPromptTimer = setTimeout(() => {
            metaMaskHelperMessage.style.display = 'block';
        }, 7000); // 7 seconds delay

        // --- Step 3: Send the transaction via MetaMask ---
        const transactionHash = await window.ethereum.request({
            method: 'eth_sendTransaction',
            params: [txParams],
        });

        // If we reach here, the transaction was confirmed, so clear the timer and hide the helper
        clearTimeout(metaMaskPromptTimer);
        metaMaskHelperMessage.style.display = 'none';

        console.log('Transaction successful!');
        console.log('Transaction Hash:', transactionHash);

        statusMessage.textContent = 'Transaction successful!';
        transactionDetails.textContent = `Hash: ${transactionHash}`;
        closeTabMessage.textContent = 'You can now close this tab.';
        closeTabMessage.style.display = 'block';

        // --- Step 4: Send transaction hash back to Python server ---
        await sendShutdownSignal(`success:${transactionHash}`);

    } catch (error) {
        // In case of any error, ensure the helper message is cleared/hidden
        clearTimeout(metaMaskPromptTimer);
        metaMaskHelperMessage.style.display = 'none';

        console.error('An error occurred during the MetaMask process:', error);
        // Log the full error object for more details
        console.error('Full error object:', error);
        statusMessage.textContent = 'Transaction process failed.';
        // Provide more specific error message if available
        transactionDetails.textContent = `Error: ${error.message || error.code || 'Unknown error'}. Check MetaMask for details.`;
        consoleMessage.textContent = 'Please check the console for details.';
        closeTabMessage.textContent = 'You can now close this tab.';
        closeTabMessage.style.display = 'block';

        // --- Step 4 (cont.): Send failure status back to Python server ---
        await sendShutdownSignal(`failure:${error.message || error.code || 'unknown_error'}`);
    }
}

// Run the entire process when the script loads
runMetaMaskProcess();
