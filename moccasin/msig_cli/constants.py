################################################################
#                       ERROR CONSTANTS                        #
################################################################
ERROR_INVALID_ADDRESS = "Invalid address format. Please enter a valid checksum address."
ERROR_INVALID_RPC_URL = "Invalid RPC URL format. Please enter a valid URL starting with http:// or https://."
ERROR_INVALID_NUMBER = "Invalid number format. Please enter a valid integer."
ERROR_INVALID_NOT_ZERO_NUMBER = (
    "Invalid non zero number format. Please enter a valid non zero positive integer."
)
ERROR_INVALID_OPERATION = "Invalid operation type. Please enter a valid operation type (0 for call, 1 for delegate call)."
ERROR_INVALID_DATA = (
    "Invalid data format. Please enter a valid hex string for calldata."
)
ERROR_INVALID_TRANSACTION_TYPE = "Invalid transaction type. Please enter a valid transaction type (0 for contract call, 1 for ERC20 transfer, 2 for raw)."
ERROR_INVALID_FUNCTION_SIGNATURE = (
    "Invalid function signature. Example: transfer(address,uint256)"
)
ERROR_INVALID_BOOLEAN = "Invalid boolean value. Please enter true/false"
ERROR_INVALID_JSON_FILE = "Invalid JSON file path. Please provide a valid .json file."
ERROR_INVALID_SIGNATURES_INPUT = (
    "Invalid signatures input. Must be a valid hex string or a path to a .txt file."
)
ERROR_INVALID_TXT_FILE = (
    "Invalid transaction file path. Please provide a valid .txt file."
)
ERROR_INVALID_PRIVATE_KEY = (
    "Invalid private key format. Must be a 64-character hex string with 0x prefix."
)
ERROR_INVALID_SIGNER = (
    "Invalid signer input. Must be a valid account name or a private key."
)

################################################################
#                       PROMPT CONSTANTS                       #
################################################################
LEFT_PROMPT_SIGN = "<b><orange>msig &gt; </orange></b>"
