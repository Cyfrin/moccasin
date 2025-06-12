import os
import platform
from pathlib import Path

from moccasin.constants.chains import BLOCKSCOUT_EXPLORERS, CHAIN_INFO, ZKSYNC_EXPLORERS

# File Names
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

# OS specific
IS_WINDOWS = platform.system() == "Windows"

# Complex Vars
DEFAULT_PROJECT_FOLDERS = [
    CONTRACTS_FOLDER,
    TESTS_FOLDER,
    SCRIPT_FOLDER,
    DEPENDENCIES_FOLDER + "/" + GITHUB,
    DEPENDENCIES_FOLDER + "/" + PYPI,
]

# Default Network Vars
MOCCASIN_KEYSTORES_FOLDER_NAME = "keystores/"
FOUNDRTY_KEYSTORES_PATH = Path.home().joinpath(".foundry/keystores")
DOT_ENV_FILE = ".env"
DOT_ENV_KEY = "dot_env"
KEYSTORES_PATH_KEY = "keystores_path"
CONSOLE_HISTORY_FILE = "moccasin_history"
DEFAULT_API_KEY_ENV_VAR = "EXPLORER_API_KEY"

# Configurable Vars
MOCCASIN_DEFAULT_FOLDER = Path(
    os.getenv("MOCCASIN_DEFAULT_FOLDER", Path.home().joinpath(".moccasin/"))
)
MOCCASIN_DEFAULT_FOLDER.mkdir(parents=True, exist_ok=True)
MOCCASIN_KEYSTORE_PATH = Path(
    os.getenv(
        "MOCCASIN_KEYSTORE_PATH",
        MOCCASIN_DEFAULT_FOLDER.joinpath(MOCCASIN_KEYSTORES_FOLDER_NAME),
    )
)
MOCCASIN_KEYSTORE_PATH.mkdir(parents=True, exist_ok=True)
CONFIG_NAME = "moccasin.toml"


# Define default values for PYEVM and ERAVM
LOCAL_NETWORK_DEFAULTS = {
    PYEVM: {
        "is_zksync": False,
        "prompt_live": False,
        SAVE_TO_DB: False,
        "live_or_staging": False,
        "db_path": None,
    },
    ERAVM: {
        "is_zksync": True,
        "prompt_live": False,
        SAVE_TO_DB: False,
        "live_or_staging": False,
        "db_path": None,
    },
}
FORK_NETWORK_DEFAULTS = {
    "is_zksync": False,
    "prompt_live": False,
    SAVE_TO_DB: False,
    "live_or_staging": False,
    "db_path": None,
}
SPECIFIC_VALUES_FOR_ALL_LOCAL_NETWORKS = {SAVE_TO_DB: False, "db_path": None}
RESTRICTED_VALUES_FOR_LOCAL_NETWORK = [
    "url",
    "chain_id",
    "block_identifier",
    "fork",
    "explorer_uri",
    "exploer_api_key",
]

# Testing Vars
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

DEFAULT_NETWORKS_BY_NAME = {}

for chain_name, chain_data in CHAIN_INFO.items():
    explorer_uri = None
    explorer_type = None

    if chain_name in BLOCKSCOUT_EXPLORERS:
        explorer_uri = BLOCKSCOUT_EXPLORERS[chain_name]
        explorer_type = "blockscout"
    elif chain_name in ZKSYNC_EXPLORERS:
        explorer_uri = ZKSYNC_EXPLORERS[chain_name]
        explorer_type = "zksyncexplorer"
    else:
        continue

    DEFAULT_NETWORKS_BY_NAME[chain_name] = {
        "explorer_uri": explorer_uri,
        "explorer_type": explorer_type,
        "multicall2": chain_data["multicall2"],
        "chain_id": chain_data["chain_id"],
    }

DEFAULT_NETWORKS_BY_CHAIN_ID: dict[int, dict] = {
    network["chain_id"]: {**network, "name": name}
    for name, network in DEFAULT_NETWORKS_BY_NAME.items()
}
