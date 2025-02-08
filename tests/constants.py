from pathlib import Path

# ------------------------------------------------------------------
#                        TEST PROJECT PATH
# ------------------------------------------------------------------
COMPLEX_PROJECT_PATH = Path(__file__).parent.joinpath("data/complex_project/")
DEPLOYMENTS_PROJECT_PATH = Path(__file__).parent.joinpath("data/deployments_project/")
INSTALL_PROJECT_PATH = Path(__file__).parent.joinpath("data/installation_project/")
NO_CONFIG_PROJECT_PATH = Path(__file__).parent.joinpath("data/no_config_project/")
PURGE_PROJECT_PATH = Path(__file__).parent.joinpath("data/purge_project/")
TESTS_CONFIG_PROJECT_PATH = Path(__file__).parent.joinpath("data/tests_project/")
ZKSYNC_PROJECT_PATH = Path(__file__).parent.joinpath("data/zksync_project/")

# ------------------------------------------------------------------
#                            TEST ANVIL
# ------------------------------------------------------------------
ANVIL1_PRIVATE_KEY = (
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
)
ANVIL1_KEYSTORE_NAME = "anvil1"
ANVIL1_KEYSTORE_PASSWORD = "password"
ANVIL_STORED_STATE_PATH = Path(__file__).parent.joinpath("data/anvil_data/state.json")
ANVIL_STORED_KEYSTORE_PATH = Path(__file__).parent.joinpath(
    "data/anvil_data/anvil1.json"
)


# ------------------------------------------------------------------
#                            TEST TOML
# ------------------------------------------------------------------
INSTALLATION_STARTING_TOML = """[project]
dependencies = [
    "snekmate", 
    "moccasin", 
    "PatrickAlphaC/test_repo@0.1.1",
    "pcaversaccio/snekmate",
]

# PRESERVE COMMENTS

[networks.sepolia]
url = "https://ethereum-sepolia-rpc.publicnode.com"
chain_id = 11155111
save_to_db = false
"""

PURGE_STARTING_TOML = """[project]
dependencies = ["snekmate", "patrickalphac/test_repo"]

# PRESERVE COMMENTS

[networks.sepolia]
url = "https://ethereum-sepolia-rpc.publicnode.com"
chain_id = 11155111
"""


# ------------------------------------------------------------------
#                           TEST LIB
# ------------------------------------------------------------------
COMMENT_CONTENT = "PRESERVE COMMENTS"
NEW_VERSION = "0.0.5"
ORG_NAME = "pcaversaccio"
PIP_PACKAGE_NAME = "snekmate"
VERSION = "0.1.0"
GITHUB_PACKAGE_NAME = f"{ORG_NAME}/{PIP_PACKAGE_NAME}"
LIB_GH_PATH = "lib/github"
LIB_PIP_PATH = "lib/pypi"
MOCCASIN_LIB_NAME = "moccasin"
MOCCASIN_TOML = "moccasin.toml"
PATRICK_ORG_NAME = "patrickalphac"
PATRICK_REPO_NAME = "test_repo"
PATRICK_PACKAGE_NAME = f"{PATRICK_ORG_NAME}/{PATRICK_REPO_NAME}"
VERSIONS_TOML = "versions.toml"
