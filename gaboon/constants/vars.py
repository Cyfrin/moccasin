from pathlib import Path

# File Names
CONFIG_NAME = "gaboon.toml"
README_PATH = "README.md"
COUNTER_CONTRACT = "Counter.vy"

# Default Folder Names
BUILD_FOLDER = "out"
CONTRACTS_FOLDER = "src"
TESTS_FOLDER = "tests"
SCRIPT_FOLDER = "script"
DEPENDENCIES_FOLDER = "lib"

# Complex Vars
DEFAULT_PROJECT_FOLDERS = [CONTRACTS_FOLDER, TESTS_FOLDER, SCRIPT_FOLDER]
DEFAULT_GABOON_FOLDER = Path.home().joinpath(".gaboon/")
DEFAULT_KEYSTORES_PATH = DEFAULT_GABOON_FOLDER.joinpath("keystores/")
# TODO - add a --foundry flag for wallet commands to use foundry keystores
FOUNDRTY_KEYSTORES_PATH = Path.home().joinpath(".foundry/keystores")
# TODO: Make this configurable
DOT_ENV_FILE = ".env"
CONSOLE_HISTORY_FILE = "gaboon_history"

# Testing Vars
DEFAULT_ANVIL_PRIVATE_KEY = (
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
)
DEFAULT_ANVIL_SENDER = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"

# Installation Variables
REQUEST_HEADERS = {"User-Agent": "Gaboon"}
PACKAGE_VERSION_FILE = "versions.toml"

GABOON_GITHUB = "https://github.com/vyperlang/gaboon"


# DEFAULT_NETWORKS_BY_NAME: dict[str:dict] = {
#     "mainnet": {
#         "explorer": "https://api.etherscan.io/api",
#         "multicall2": "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696",
#         "chain_id": 1,
#     },
#     "sepolia": {
#         "explorer": "https://api-sepolia.etherscan.io/",
#         "multicall2": None,
#         "chain_id": 11155111,
#     },
#     "goerli": {
#         "explorer": "https://api-goerli.etherscan.io/api",
#         "multicall2": "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696",
#         "chain_id": 5,
#     },
#     "etc": {
#         "explorer": "https://blockscout.com/etc/mainnet/api",
#         "multicall2": None,
#         "chain_id": 61,
#     },
#     "kotti": {
#         "explorer": "https://blockscout.com/etc/kotti/api",
#         "multicall2": None,
#         "chain_id": 6,
#     },
#     "arbitrum": {
#         "explorer": "https://api.arbiscan.io/api",
#         "multicall2": "0x5B5CFE992AdAC0C9D48E05854B2d91C73a003858",
#         "chain_id": 42161,
#     },
#     "avax-main": {
#         "explorer": "https://api.snowtrace.io/api",
#         "multicall2": None,
#         "chain_id": 43114,
#     },
#     "avax-test": {"explorer": None, "multicall2": None, "chain_id": 43113},
#     "aurora-main": {
#         "explorer": "https://api.aurorascan.dev/api",
#         "multicall2": "0xace58a26b8Db90498eF0330fDC9C2655db0C45E2",
#         "chain_id": 1313161554,
#     },
#     "aurora-test": {
#         "explorer": "https://testnet.aurorascan.dev/api",
#         "multicall2": None,
#         "chain_id": 1313161555,
#     },
#     "bsc-test": {
#         "explorer": "https://api-testnet.bscscan.com/api",
#         "multicall2": None,
#         "chain_id": 97,
#     },
#     "bsc-main": {
#         "explorer": "https://api.bscscan.com/api",
#         "multicall2": None,
#         "chain_id": 56,
#     },
#     "boba-test": {
#         "explorer": "https://blockexplorer.rinkeby.boba.network/api",
#         "multicall2": "0xeD188A73c442Df375b19b7b8f394a15a2b851BB5",
#         "chain_id": 28,
#     },
#     "boba-main": {
#         "explorer": "https://blockexplorer.boba.network/api",
#         "multicall2": "0xbe2Be647F8aC42808E67431B4E1D6c19796bF586",
#         "chain_id": 288,
#     },
#     "ftm-test": {
#         "explorer": "https://explorer.testnet.fantom.network",
#         "multicall2": None,
#         "chain_id": 4050,
#     },
#     "ftm-main": {
#         "explorer": "https://api.ftmscan.com/api",
#         "multicall2": None,
#         "chain_id": 250,
#     },
#     "harmony-main": {
#         "explorer": None,
#         "multicall2": "0x3E01dD8a5E1fb3481F0F589056b428Fc308AF0Fb",
#         "chain_id": 1666600000,
#     },
#     "hedera-main": {
#         "explorer": "https://hashscan.io/mainnet",
#         "multicall2": None,
#         "chain_id": 295,
#     },
#     "hedera-test": {
#         "explorer": "https://hashscan.io/testnet",
#         "multicall2": None,
#         "chain_id": 296,
#     },
#     "hedera-preview": {
#         "explorer": "https://hashscan.io/previewnet",
#         "multicall2": None,
#         "chain_id": 297,
#     },
#     "moonbeam-main": {
#         "explorer": "https://api-moonbeam.moonscan.io/api",
#         "multicall2": "0x1337BedC9D22ecbe766dF105c9623922A27963EC",
#         "chain_id": 1284,
#     },
#     "moonbeam-test": {
#         "explorer": "https://api-moonbase.moonscan.io/api",
#         "multicall2": "0x37084d0158C68128d6Bc3E5db537Be996f7B6979",
#         "chain_id": 1287,
#     },
#     "moonriver-main": {
#         "explorer": "https://api-moonriver.moonscan.io/api",
#         "multicall2": "0xaef00a0cf402d9dedd54092d9ca179be6f9e5ce3",
#         "chain_id": 1285,
#     },
#     "optimism-main": {
#         "explorer": "https://api-optimistic.etherscan.io/api",
#         "multicall2": "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
#         "chain_id": 10,
#     },
#     "optimism-test": {
#         "explorer": "https://api-goerli-optimism.etherscan.io/api",
#         "multicall2": "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
#         "chain_id": 420,
#     },
#     "polygon-main": {
#         "explorer": "https://api.polygonscan.com/api",
#         "multicall2": "0xc8E51042792d7405184DfCa245F2d27B94D013b6",
#         "chain_id": 137,
#     },
#     "polygon-test": {
#         "explorer": "https://api-testnet.polygonscan.com/api",
#         "multicall2": "0x6842E0412AC1c00464dc48961330156a07268d14",
#         "chain_id": 80001,
#     },
#     "gnosis-main": {
#         "explorer": "https://api.gnosisscan.io/api",
#         "multicall2": None,
#         "chain_id": 100,
#     },
#     "gnosis-test": {
#         "explorer": "https://gnosis-chiado.blockscout.com/api",
#         "multicall2": None,
#         "chain_id": 10200,
#     },
#     "base-main": {
#         "explorer": "https://api.basescan.org/api",
#         "multicall2": None,
#         "chain_id": 8453,
#     },
# }

# DEFAULT_NETWORKS_BY_CHAIN_ID: dict[int, dict] = {
#     1: {
#         "name": "mainnet",
#         "explorer": "https://api.etherscan.io/api",
#         "multicall2": "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696",
#     },
#     11155111: {
#         "name": "sepolia",
#         "explorer": "https://api-sepolia.etherscan.io/",
#         "multicall2": None,
#     },
#     5: {
#         "name": "goerli",
#         "explorer": "https://api-goerli.etherscan.io/api",
#         "multicall2": "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696",
#     },
#     61: {
#         "name": "etc",
#         "explorer": "https://blockscout.com/etc/mainnet/api",
#         "multicall2": None,
#     },
#     6: {
#         "name": "kotti",
#         "explorer": "https://blockscout.com/etc/kotti/api",
#         "multicall2": None,
#     },
#     42161: {
#         "name": "arbitrum",
#         "explorer": "https://api.arbiscan.io/api",
#         "multicall2": "0x5B5CFE992AdAC0C9D48E05854B2d91C73a003858",
#     },
#     43114: {
#         "name": "avax-main",
#         "explorer": "https://api.snowtrace.io/api",
#         "multicall2": None,
#     },
#     43113: {
#         "name": "avax-test",
#         "explorer": None,
#         "multicall2": None,
#     },
#     1313161554: {
#         "name": "aurora-main",
#         "explorer": "https://api.aurorascan.dev/api",
#         "multicall2": "0xace58a26b8Db90498eF0330fDC9C2655db0C45E2",
#     },
#     1313161555: {
#         "name": "aurora-test",
#         "explorer": "https://testnet.aurorascan.dev/api",
#         "multicall2": None,
#     },
#     97: {
#         "name": "bsc-test",
#         "explorer": "https://api-testnet.bscscan.com/api",
#         "multicall2": None,
#     },
#     56: {
#         "name": "bsc-main",
#         "explorer": "https://api.bscscan.com/api",
#         "multicall2": None,
#     },
#     28: {
#         "name": "boba-test",
#         "explorer": "https://blockexplorer.rinkeby.boba.network/api",
#         "multicall2": "0xeD188A73c442Df375b19b7b8f394a15a2b851BB5",
#     },
#     288: {
#         "name": "boba-main",
#         "explorer": "https://blockexplorer.boba.network/api",
#         "multicall2": "0xbe2Be647F8aC42808E67431B4E1D6c19796bF586",
#     },
#     4050: {
#         "name": "ftm-test",
#         "explorer": "https://explorer.testnet.fantom.network",
#         "multicall2": None,
#     },
#     250: {
#         "name": "ftm-main",
#         "explorer": "https://api.ftmscan.com/api",
#         "multicall2": None,
#     },
#     1666600000: {
#         "name": "harmony-main",
#         "explorer": None,
#         "multicall2": "0x3E01dD8a5E1fb3481F0F589056b428Fc308AF0Fb",
#     },
#     295: {
#         "name": "hedera-main",
#         "explorer": "https://hashscan.io/mainnet",
#         "multicall2": None,
#     },
#     296: {
#         "name": "hedera-test",
#         "explorer": "https://hashscan.io/testnet",
#         "multicall2": None,
#     },
#     297: {
#         "name": "hedera-preview",
#         "explorer": "https://hashscan.io/previewnet",
#         "multicall2": None,
#     },
#     1284: {
#         "name": "moonbeam-main",
#         "explorer": "https://api-moonbeam.moonscan.io/api",
#         "multicall2": "0x1337BedC9D22ecbe766dF105c9623922A27963EC",
#     },
#     1287: {
#         "name": "moonbeam-test",
#         "explorer": "https://api-moonbase.moonscan.io/api",
#         "multicall2": "0x37084d0158C68128d6Bc3E5db537Be996f7B6979",
#     },
#     1285: {
#         "name": "moonriver-main",
#         "explorer": "https://api-moonriver.moonscan.io/api",
#         "multicall2": "0xaef00a0cf402d9dedd54092d9ca179be6f9e5ce3",
#     },
#     10: {
#         "name": "optimism-main",
#         "explorer": "https://api-optimistic.etherscan.io/api",
#         "multicall2": "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
#     },
#     420: {
#         "name": "optimism-test",
#         "explorer": "https://api-goerli-optimism.etherscan.io/api",
#         "multicall2": "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
#     },
#     137: {
#         "name": "polygon-main",
#         "explorer": "https://api.polygonscan.com/api",
#         "multicall2": "0xc8E51042792d7405184DfCa245F2d27B94D013b6",
#     },
#     80001: {
#         "name": "polygon-test",
#         "explorer": "https://api-testnet.polygonscan.com/api",
#         "multicall2": "0x6842E0412AC1c00464dc48961330156a07268d14",
#     },
#     100: {
#         "name": "gnosis-main",
#         "explorer": "https://api.gnosisscan.io/api",
#         "multicall2": None,
#     },
#     10200: {
#         "name": "gnosis-test",
#         "explorer": "https://gnosis-chiado.blockscout.com/api",
#         "multicall2": None,
#     },
#     8453: {
#         "name": "base-main",
#         "explorer": "https://api.basescan.org/api",
#         "multicall2": None,
#     },
# }
