import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

import moccasin.constants.vars as vars
from moccasin.commands.wallet import save_to_keystores
from moccasin.config import Config, _set_config, initialize_global_config
from moccasin.constants.vars import DEPENDENCIES_FOLDER
from tests.utils.anvil import ANVIL_URL, AnvilProcess

COMPLEX_PROJECT_PATH = Path(__file__).parent.joinpath("data/complex_project/")
DEPLOYMENTS_PROJECT_PATH = Path(__file__).parent.joinpath("data/deployments_project/")
INSTALL_PROJECT_PATH = Path(__file__).parent.joinpath("data/installation_project/")
PURGE_PROJECT_PATH = Path(__file__).parent.joinpath("data/purge_project/")
ZKSYNC_PROJECT_PATH = Path(__file__).parent.joinpath("data/zksync_project/")
ANVIL1_PRIVATE_KEY = (
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
)
ANVIL1_KEYSTORE_NAME = "anvil1"
ANVIL1_KEYSTORE_PASSWORD = "password"
ANVIL_KEYSTORE_SAVED = {
    "address": "f39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    "crypto": {
        "cipher": "aes-128-ctr",
        "cipherparams": {"iv": "c9f63a81441a72e632b1635a662c9633"},
        "ciphertext": "231713ea92116c583f12e5d2ecc2f542a78a2ab9c75f834b763edda57f2557e2",
        "kdf": "scrypt",
        "kdfparams": {
            "dklen": 32,
            "n": 262144,
            "r": 8,
            "p": 1,
            "salt": "b0da783cd79eb9b2a8cdb5e215c083a7",
        },
        "mac": "f65aec3ade028a51c0002c322063c28d5aeb927b685d57b0d8448810ee6a2884",
    },
    "id": "27ea3a2d-e080-402a-a607-ee7caf8d0a06",
    "version": 3,
}
ANVIL_STORED_STATE_PATH = Path(__file__).parent.joinpath("data/anvil_data/state.json")

INSTALLATION_STARTING_TOML = """[project]
dependencies = ["snekmate", "moccasin"]

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

pip_package_name = "snekmate"
org_name = "pcaversaccio"
github_package_name = f"{org_name}/{pip_package_name}"
version = "0.1.0"
new_version = "0.0.5"
comment_content = "PRESERVE COMMENTS"
patrick_org_name = "patrickalphac"
patrick_repo_name = "test_repo"
patrick_package_name = f"{patrick_org_name}/{patrick_repo_name}"


# ------------------------------------------------------------------
#                         BASIC FIXTURES
# ------------------------------------------------------------------
@pytest.fixture(scope="session")
def session_monkeypatch():
    monkeypatch = pytest.MonkeyPatch()
    yield monkeypatch
    monkeypatch.undo()


@pytest.fixture(scope="session")
def anvil_keystore(session_monkeypatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        save_to_keystores(
            ANVIL1_KEYSTORE_NAME,
            ANVIL1_PRIVATE_KEY,
            password=ANVIL1_KEYSTORE_PASSWORD,
            keystores_path=Path(temp_dir),
        )
        session_monkeypatch.setattr(vars, "DEFAULT_KEYSTORES_PATH", Path(temp_dir))
        yield Path(temp_dir)


@pytest.fixture(scope="session")
def set_fake_chain_rpc(session_monkeypatch):
    session_monkeypatch.setenv("FAKE_CHAIN_RPC_URL", ANVIL_URL)
    yield


@pytest.fixture(scope="session")
def mox_path():
    return os.path.join(os.path.dirname(sys.executable), "mox")


# ------------------------------------------------------------------
#                    COMPLEX PROJECT FIXTURES
# ------------------------------------------------------------------
@pytest.fixture(scope="session")
def complex_project_config() -> Config:
    test_db_path = os.path.join(COMPLEX_PROJECT_PATH, ".deployments.db")

    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    config = initialize_global_config(COMPLEX_PROJECT_PATH)
    return config


@pytest.fixture(scope="session")
def complex_out_folder(complex_project_config) -> Config:
    return complex_project_config.out_folder


@pytest.fixture
def complex_cleanup_coverage():
    yield
    coverage_file = COMPLEX_PROJECT_PATH.joinpath(".coverage")
    if os.path.exists(coverage_file):
        os.remove(coverage_file)


@pytest.fixture
def complex_cleanup_out_folder(complex_out_folder):
    yield
    created_folder_path = COMPLEX_PROJECT_PATH.joinpath(complex_out_folder)
    if os.path.exists(created_folder_path):
        shutil.rmtree(created_folder_path)


@pytest.fixture
def complex_cleanup_dependencies_folder():
    yield
    created_folder_path = COMPLEX_PROJECT_PATH.joinpath(DEPENDENCIES_FOLDER)
    if os.path.exists(created_folder_path):
        shutil.rmtree(created_folder_path)


CONFTEST_OVERRIDE_FILE = """import pytest
from script.deploy import deploy
from script.deploy_coffee import deploy as deploy_coffee

from moccasin.fixture_tools import request_fixtures

request_fixtures(["price_feed", ("price_feed", "eth_usd"), ("price_feed", "eth_usd")], scope="session")


@pytest.fixture
def counter_contract():
    return deploy()


@pytest.fixture
def coffee():
    return deploy_coffee()
"""


@pytest.fixture
def complex_conftest_override():
    conftest_path = COMPLEX_PROJECT_PATH.joinpath("tests/conftest.py")
    original_content = conftest_path.read_text()
    with open(conftest_path, "w") as f:
        f.write(CONFTEST_OVERRIDE_FILE)
    yield
    with open(conftest_path, "w") as f:
        f.write(original_content)


# ------------------------------------------------------------------
#                     INSTALLATION PROJECT FIXTURES
# ------------------------------------------------------------------
@pytest.fixture(scope="session")
def installation_project_config() -> Config:
    test_db_path = os.path.join(INSTALL_PROJECT_PATH, ".deployments.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    return initialize_global_config(INSTALL_PROJECT_PATH)


@pytest.fixture
def installation_cleanup_dependencies():
    yield
    created_folder_path = INSTALL_PROJECT_PATH.joinpath(DEPENDENCIES_FOLDER)
    with open(INSTALL_PROJECT_PATH.joinpath("moccasin.toml"), "w") as f:
        f.write(INSTALLATION_STARTING_TOML)
    if os.path.exists(created_folder_path):
        shutil.rmtree(created_folder_path)


# ------------------------------------------------------------------
#                         PURGE PROJECT FIXTURES
# ------------------------------------------------------------------
@pytest.fixture(scope="session")
def purge_project_config() -> Config:
    test_db_path = os.path.join(PURGE_PROJECT_PATH, ".deployments.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    return initialize_global_config(PURGE_PROJECT_PATH)


@pytest.fixture
def purge_reset_dependencies():
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        # Copy the entire project directory to the temporary location
        shutil.copytree(
            PURGE_PROJECT_PATH, temp_path / PURGE_PROJECT_PATH.name, dirs_exist_ok=True
        )
        yield
        for item in (temp_path / PURGE_PROJECT_PATH.name).iterdir():
            if item.is_dir():
                shutil.rmtree(PURGE_PROJECT_PATH / item.name, ignore_errors=True)
                shutil.copytree(
                    item, PURGE_PROJECT_PATH / item.name, dirs_exist_ok=True
                )
            else:
                shutil.copy2(item, PURGE_PROJECT_PATH / item.name)

        with open(PURGE_PROJECT_PATH.joinpath("moccasin.toml"), "w") as f:
            f.write(PURGE_STARTING_TOML)


# ------------------------------------------------------------------
#                      DEPLOYMENTS PROJECT FIXTURES
# ------------------------------------------------------------------
@pytest.fixture(scope="session")
def deployments_project_config_read() -> Generator[Config, None, None]:
    """We need to copy the starting database to a test database before running the tests.

    And then, initialize the config file from the moccasin.toml

    At the end, we should reset the test database to the starting database.
    """
    starting_db_path = os.path.join(
        DEPLOYMENTS_PROJECT_PATH, ".starting_deployments.db"
    )
    test_db_path = os.path.join(DEPLOYMENTS_PROJECT_PATH, ".deployments.db")

    if not os.path.exists(starting_db_path):
        raise FileNotFoundError(f"Starting database not found: {starting_db_path}")
    shutil.copy2(starting_db_path, test_db_path)

    config = _set_config(DEPLOYMENTS_PROJECT_PATH)

    yield config

    if os.path.exists(test_db_path):
        os.remove(test_db_path)


COUNTER_CONTRACT_OVERRIDE = """
# SPDX-License-Identifier: MIT
# pragma version 0.4.0

number: public(uint256)

@external
def set_number(new_number: uint256):
    self.number = new_number

# This function is slightly different
@external
def increment():
    self.number += 2
"""


@pytest.fixture
def deployments_contract_override():
    counter_contract = DEPLOYMENTS_PROJECT_PATH.joinpath("src/Counter.vy")
    original_content = counter_contract.read_text()
    with open(counter_contract, "w") as f:
        f.write(COUNTER_CONTRACT_OVERRIDE)
    yield
    with open(counter_contract, "w") as f:
        f.write(original_content)


@pytest.fixture(scope="session")
def deployments_project_config_write() -> Generator[Config, None, None]:
    """We need to copy the starting database to a test database before running the tests.

    And then, initialize the config file from the moccasin.toml

    At the end, we should reset the test database to the starting database.
    """
    starting_db_path = os.path.join(
        DEPLOYMENTS_PROJECT_PATH, ".starting_deployments.db"
    )
    test_db_path = os.path.join(DEPLOYMENTS_PROJECT_PATH, ".deployments.db")

    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    if not os.path.exists(starting_db_path):
        raise FileNotFoundError(f"Starting database not found: {starting_db_path}")
    shutil.copy2(starting_db_path, test_db_path)

    config = _set_config(DEPLOYMENTS_PROJECT_PATH)

    yield config

    if os.path.exists(test_db_path):
        os.remove(test_db_path)


# ------------------------------------------------------------------
#                             ANVIL
# ------------------------------------------------------------------
@pytest.fixture(scope="module")
def anvil_process():
    with AnvilProcess(args=["--load-state", str(ANVIL_STORED_STATE_PATH)]):
        yield


@pytest.fixture(scope="function")
def anvil_process_reset():
    with AnvilProcess(args=["--load-state", str(ANVIL_STORED_STATE_PATH)]):
        yield


@pytest.fixture
def anvil_two_no_state():
    with AnvilProcess(args=["-p", "8546"]):
        yield
