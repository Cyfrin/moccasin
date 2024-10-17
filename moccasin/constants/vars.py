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
SAVE_TO_DB = "save_to_db"
DEFAULT_NETWORK = PYEVM
DB_PATH_LOCAL_DEFAULT = ":memory:"
DB_PATH_LIVE_DEFAULT = ".deployments.db"

# Project Config Keys
SAVE_ABI_PATH = "save_abi_path"

# Tests folder is always tests
TESTS_FOLDER = "tests"

# Installation Variables
REQUEST_HEADERS = {"User-Agent": "Moccasin"}
PACKAGE_VERSION_FILE = "versions.toml"
PYPI = "pypi"
GITHUB = "github"

# Complex Vars
DEFAULT_PROJECT_FOLDERS = [
    CONTRACTS_FOLDER,
    TESTS_FOLDER,
    SCRIPT_FOLDER,
    DEPENDENCIES_FOLDER + "/" + GITHUB,
    DEPENDENCIES_FOLDER + "/" + PYPI,
]

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
MOCCASIN_GITHUB = "https://github.com/cyfrin/moccasin"
STARTING_BOA_BALANCE = 1000000000000000000000  # 1,000 Ether

# Database vars
GET_CONTRACT_SQL = "SELECT {} FROM deployments {}ORDER BY broadcast_ts DESC {}"
SQL_WHERE = "WHERE "
SQL_CONTRACT_NAME = "contract_name = ? "
SQL_AND = "AND "
SQL_CHAIN_ID = "json_extract(tx_dict, '$.chainId') = ? "
SQL_LIMIT = "LIMIT ? "

# Networking defaults
DEFAULT_NETWORKS_BY_NAME: dict[str, dict] = {
    "mainnet": {
        "explorer": "https://eth.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696",
        "chain_id": 1,
    },
    "sepolia": {
        "explorer": "https://eth-sepolia.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 11155111,
    },
    "goerli": {
        "explorer": "https://eth-goerli.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696",
        "chain_id": 5,
    },
    "arbitrum": {
        "explorer": "https://arbitrum.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": "0x5B5CFE992AdAC0C9D48E05854B2d91C73a003858",
        "chain_id": 42161,
    },
    "optimism-main": {
        "explorer": "https://optimism.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
        "chain_id": 10,
    },
    "optimism-test": {
        "explorer": "https://optimism-sepolia.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
        "chain_id": 420,
    },
    "polygon-main": {
        "explorer": "https://polygon.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": "0xc8E51042792d7405184DfCa245F2d27B94D013b6",
        "chain_id": 137,
    },
    "gnosis-main": {
        "explorer": "https://gnosis.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 100,
    },
    "gnosis-test": {
        "explorer": "https://gnosis-chiado.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 10200,
    },
    "base-main": {
        "explorer": "https://base.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 8453,
    },
    "syscoin": {
        "explorer": "https://explorer.syscoin.org/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 57,
    },
    "ethereumclassic": {
        "explorer": "https://etc.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 61,
    },
    "nova-network": {
        "explorer": "https://explorer.novanetwork.io/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 87,
    },
    "velas": {
        "explorer": "https://evmexplorer.velas.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 106,
    },
    "thundercore": {
        "explorer": "https://explorer-mainnet.thundercore.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 108,
    },
    "fuse": {
        "explorer": "https://explorer.fuse.io/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 122,
    },
    "heco": {"explorer": None, "multicall2": None, "chain_id": 128},
    "shimmer_evm": {
        "explorer": "https://explorer.evm.shimmer.network/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 148,
    },
    "manta": {
        "explorer": "https://pacific-explorer.manta.network/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 169,
    },
    "energyweb": {
        "explorer": "https://explorer.energyweb.org/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 246,
    },
    "oasys": {
        "explorer": "https://explorer.oasys.games/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 248,
    },
    "omax": {"explorer": "https://omaxscan.com/", "multicall2": None, "chain_id": 311},
    "filecoin": {
        "explorer": "https://filecoin.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 314,
    },
    "kucoin": {"explorer": "https://scan.kcc.io/", "multicall2": None, "chain_id": 321},
    "zksync-era": {
        "explorer": "https://zksync2-mainnet-explorer.zksync.io",
        "explorer_type": "zksyncexplorer",
        "multicall2": None,
        "chain_id": 324,
    },
    "sepolia-zksync-era": {
        "explorer": "https://explorer.sepolia.era.zksync.dev",
        "explorer_type": "zksyncexplorer",
        "multicall2": None,
        "chain_id": 300,
    },
    "shiden": {
        "explorer": "https://shiden.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 336,
    },
    "rollux": {
        "explorer": "https://explorer.rollux.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 570,
    },
    "astar": {
        "explorer": "https://astar.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 592,
    },
    "callisto": {
        "explorer": "https://explorer.callisto.network/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 820,
    },
    "lyra-chain": {
        "explorer": "https://explorer.lyra.finance/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 957,
    },
    "bifrost": {
        "explorer": "https://explorer.mainnet.bifrostnetwork.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 996,
    },
    "metis": {
        "explorer": "https://andromeda-explorer.metis.io/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 1088,
    },
    "polygon-zkevm": {
        "explorer": "https://zkevm.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 1101,
    },
    "core": {"explorer": None, "multicall2": None, "chain_id": 1116},
    "lisk": {
        "explorer": "https://blockscout.lisk.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 1135,
    },
    "reya-network": {
        "explorer": "https://explorer.reya.network/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 1729,
    },
    "onus": {
        "explorer": "https://explorer.onuschain.io/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 1975,
    },
    "hubblenet": {"explorer": None, "multicall2": None, "chain_id": 1992},
    "sanko": {
        "explorer": "https://explorer.sanko.xyz/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 1996,
    },
    "dogechain": {
        "explorer": "https://explorer.dogechain.dog/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 2000,
    },
    "milkomeda": {
        "explorer": "https://explorer-mainnet-cardano-evm.c1.milkomeda.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 2001,
    },
    "kava": {
        "explorer": "https://testnet.kavascan.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 2222,
    },
    "mantle": {
        "explorer": "https://explorer.mantle.xyz/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 5000,
    },
    "zetachain": {
        "explorer": "https://zetachain.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 7000,
    },
    "celo": {
        "explorer": "https://explorer.celo.org/mainnet/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 42220,
    },
    "oasis": {
        "explorer": "https://explorer.emerald.oasis.dev/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 42262,
    },
    "linea": {
        "explorer": "https://explorer.linea.build/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 59144,
    },
    "blast": {
        "explorer": "https://blast.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 81457,
    },
    "taiko": {
        "explorer": "https://blockscoutapi.mainnet.taiko.xyz/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 167000,
    },
    "scroll": {
        "explorer": "https://blockscout.scroll.io/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 534352,
    },
    "zora": {
        "explorer": "https://explorer.zora.energy/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 7777777,
    },
    "neon": {
        "explorer": "https://neon.blockscout.com/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 245022934,
    },
    "aurora": {
        "explorer": "https://explorer.mainnet.aurora.dev/",
        "explorer_type": "blockscout",
        "multicall2": None,
        "chain_id": 1313161554,
    },
}

DEFAULT_NETWORKS_BY_CHAIN_ID: dict[int, dict] = {
    network["chain_id"]: {**network, "name": name}
    for name, network in DEFAULT_NETWORKS_BY_NAME.items()
}
