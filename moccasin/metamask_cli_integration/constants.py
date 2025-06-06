# Global Constants for MetaMask UI Server Communication

HEARTBEAT_INTERVAL_CLIENT_MS = 5000  # JS client heartbeat interval (5 seconds)
HEARTBEAT_TIMEOUT_SERVER_S = (
    15  # Python server timeout for client heartbeat (15 seconds)
)

# --- Timeout Constants based on HEARTBEAT_TIMEOUT_SERVER_S ---
NETWORK_SYNC_TIMEOUT_S = (
    HEARTBEAT_TIMEOUT_SERVER_S * 5
)  # 75 seconds for initial network synchronization
ACCOUNT_CONNECTION_TIMEOUT_S = (
    HEARTBEAT_TIMEOUT_SERVER_S * 2
)  # 30 seconds for account connection after sync
TRANSACTION_CONFIRMATION_TIMEOUT_S = (
    HEARTBEAT_TIMEOUT_SERVER_S * 10
)  # 150 seconds for user to confirm a transaction
