from pathlib import Path

# File Names
CONFIG_NAME = "moccasin.toml"
README_PATH = "README.md"
COUNTER_CONTRACT = "Counter.vy"

# Default Project Values
BUILD_FOLDER = "out"
CONTRACTS_FOLDER = "src"
SCRIPT_FOLDER = "script"
DEPENDENCIES_FOLDER = "lib"
PYEVM = "pyevm"
ERAVM = "eravm"
DEFAULT_NETWORK = PYEVM

# Project Config Keys
SAVE_ABI_PATH = "save_abi_path"

# Tests folder is always tests
TESTS_FOLDER = "tests"

# Complex Vars
DEFAULT_PROJECT_FOLDERS = [CONTRACTS_FOLDER, TESTS_FOLDER, SCRIPT_FOLDER]
DEFAULT_MOCCASIN_FOLDER = Path.home().joinpath(".moccasin/")
DEFAULT_KEYSTORES_PATH = DEFAULT_MOCCASIN_FOLDER.joinpath("keystores/")
FOUNDRTY_KEYSTORES_PATH = Path.home().joinpath(".foundry/keystores")
DOT_ENV_FILE = ".env"
DOT_ENV_KEY = "dot_env"
CONSOLE_HISTORY_FILE = "moccasin_history"
DEFAULT_API_KEY_ENV_VAR = "EXPLORER_API_KEY"
RESTRICTED_VALUES_FOR_LOCAL_NETWORK = [
    "url",
    "chain_id",
    "is_fork",
    "prompt_live",
    "explorer_uri",
    "exploer_api_key",
]

# Testing Vars
ERA_DEFAULT_PRIVATE_KEY = (
    "0x3d3cbc973389cb26f657686445bcc75662b415b656078503592ac8c1abb8810e"
)
DEFAULT_ANVIL_PRIVATE_KEY = (
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
)
DEFAULT_ANVIL_SENDER = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"

# Installation Variables
REQUEST_HEADERS = {"User-Agent": "Moccasin"}
PACKAGE_VERSION_FILE = "versions.toml"
PYPI = "pypi"
GITHUB = "github"

MOCCASIN_GITHUB = "https://github.com/cyfrin/moccasin"

# Networking defaults
DEFAULT_NETWORKS_BY_NAME: dict[str, dict] = {
    "mainnet": {
        "explorer": "https://api.etherscan.io/api",
        "multicall2": "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696",
        "chain_id": 1,
    },
    "sepolia": {
        "explorer": "https://api-sepolia.etherscan.io/",
        "multicall2": None,
        "chain_id": 11155111,
    },
    "goerli": {
        "explorer": "https://api-goerli.etherscan.io/api",
        "multicall2": "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696",
        "chain_id": 5,
    },
    "arbitrum": {
        "explorer": "https://api.arbiscan.io/api",
        "multicall2": "0x5B5CFE992AdAC0C9D48E05854B2d91C73a003858",
        "chain_id": 42161,
    },
    "bsc-test": {
        "explorer": "https://api-testnet.bscscan.com/api",
        "multicall2": None,
        "chain_id": 97,
    },
    "bsc-main": {
        "explorer": "https://api.bscscan.com/api",
        "multicall2": None,
        "chain_id": 56,
    },
    "moonbeam-main": {
        "explorer": "https://api-moonbeam.moonscan.io/api",
        "multicall2": "0x1337BedC9D22ecbe766dF105c9623922A27963EC",
        "chain_id": 1284,
    },
    "moonbeam-test": {
        "explorer": "https://api-moonbase.moonscan.io/api",
        "multicall2": "0x37084d0158C68128d6Bc3E5db537Be996f7B6979",
        "chain_id": 1287,
    },
    "moonriver-main": {
        "explorer": "https://api-moonriver.moonscan.io/api",
        "multicall2": "0xaef00a0cf402d9dedd54092d9ca179be6f9e5ce3",
        "chain_id": 1285,
    },
    "optimism-main": {
        "explorer": "https://api-optimistic.etherscan.io/api",
        "multicall2": "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
        "chain_id": 10,
    },
    "optimism-test": {
        "explorer": "https://api-goerli-optimism.etherscan.io/api",
        "multicall2": "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
        "chain_id": 420,
    },
    "polygon-main": {
        "explorer": "https://api.polygonscan.com/api",
        "multicall2": "0xc8E51042792d7405184DfCa245F2d27B94D013b6",
        "chain_id": 137,
    },
    "polygon-test": {
        "explorer": "https://api-testnet.polygonscan.com/api",
        "multicall2": "0x6842E0412AC1c00464dc48961330156a07268d14",
        "chain_id": 80001,
    },
    "gnosis-main": {
        "explorer": "https://api.gnosisscan.io/api",
        "multicall2": None,
        "chain_id": 100,
    },
    "gnosis-test": {
        "explorer": "https://gnosis-chiado.blockscout.com/api",
        "multicall2": None,
        "chain_id": 10200,
    },
    "base-main": {
        "explorer": "https://api.basescan.org/api",
        "multicall2": None,
        "chain_id": 8453,
    },
}

DEFAULT_NETWORKS_BY_CHAIN_ID: dict[int, dict] = {
    1: {
        "name": "mainnet",
        "explorer": "https://api.etherscan.io/api",
        "multicall2": "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696",
    },
    11155111: {
        "name": "sepolia",
        "explorer": "https://api-sepolia.etherscan.io/",
        "multicall2": None,
    },
    5: {
        "name": "goerli",
        "explorer": "https://api-goerli.etherscan.io/api",
        "multicall2": "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696",
    },
    42161: {
        "name": "arbitrum",
        "explorer": "https://api.arbiscan.io/api",
        "multicall2": "0x5B5CFE992AdAC0C9D48E05854B2d91C73a003858",
    },
    97: {
        "name": "bsc-test",
        "explorer": "https://api-testnet.bscscan.com/api",
        "multicall2": None,
    },
    56: {
        "name": "bsc-main",
        "explorer": "https://api.bscscan.com/api",
        "multicall2": None,
    },
    1284: {
        "name": "moonbeam-main",
        "explorer": "https://api-moonbeam.moonscan.io/api",
        "multicall2": "0x1337BedC9D22ecbe766dF105c9623922A27963EC",
    },
    1287: {
        "name": "moonbeam-test",
        "explorer": "https://api-moonbase.moonscan.io/api",
        "multicall2": "0x37084d0158C68128d6Bc3E5db537Be996f7B6979",
    },
    1285: {
        "name": "moonriver-main",
        "explorer": "https://api-moonriver.moonscan.io/api",
        "multicall2": "0xaef00a0cf402d9dedd54092d9ca179be6f9e5ce3",
    },
    10: {
        "name": "optimism-main",
        "explorer": "https://api-optimistic.etherscan.io/api",
        "multicall2": "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
    },
    420: {
        "name": "optimism-test",
        "explorer": "https://api-goerli-optimism.etherscan.io/api",
        "multicall2": "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
    },
    137: {
        "name": "polygon-main",
        "explorer": "https://api.polygonscan.com/api",
        "multicall2": "0xc8E51042792d7405184DfCa245F2d27B94D013b6",
    },
    80001: {
        "name": "polygon-test",
        "explorer": "https://api-testnet.polygonscan.com/api",
        "multicall2": "0x6842E0412AC1c00464dc48961330156a07268d14",
    },
    100: {
        "name": "gnosis-main",
        "explorer": "https://api.gnosisscan.io/api",
        "multicall2": None,
    },
    10200: {
        "name": "gnosis-test",
        "explorer": "https://gnosis-chiado.blockscout.com/api",
        "multicall2": None,
    },
    8453: {
        "name": "base-main",
        "explorer": "https://api.basescan.org/api",
        "multicall2": None,
    },
}
