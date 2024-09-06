from pathlib import Path
import pytest
import os
import sys
import shutil
from gaboon.constants.vars import DEPENDENCIES_FOLDER
import gaboon.constants.vars as vars
from gaboon.commands.wallet import save_to_keystores
import tempfile
from tests.utils.anvil import ANVIL_URL
from gaboon.config import Config, initialize_global_config

COMPLEX_PROJECT_PATH = Path(__file__).parent.joinpath("data/complex_project/")
INSTALL_PROJECT_PATH = Path(__file__).parent.joinpath("data/installation_project/")
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

## BASIC FIXTURES
@pytest.fixture
def anvil_keystore(monkeypatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        save_to_keystores(
            ANVIL1_KEYSTORE_NAME,
            ANVIL1_PRIVATE_KEY,
            password=ANVIL1_KEYSTORE_PASSWORD,
            keystores_path=Path(temp_dir),
        )
        monkeypatch.setattr(vars, "DEFAULT_KEYSTORES_PATH", Path(temp_dir))
        yield Path(temp_dir)

@pytest.fixture
def anvil_fork(monkeypatch):
    monkeypatch.setenv("FAKE_CHAIN_RPC_URL", ANVIL_URL)
    yield

@pytest.fixture(scope="session")
def gab_path():
    return os.path.join(os.path.dirname(sys.executable), "gab")


## COMPLEX PROJECT FIXTURES

@pytest.fixture(scope="session")
def complex_project_config() -> Config:
    return initialize_global_config(COMPLEX_PROJECT_PATH)

@pytest.fixture(scope="session")
def complex_out_folder(complex_project_config) -> Config:
    return complex_project_config.out_folder

@pytest.fixture
def complex_cleanup_out_folder(complex_out_folder):
    yield
    created_folder_path = COMPLEX_PROJECT_PATH.joinpath(complex_out_folder)
    if os.path.exists(created_folder_path):
        shutil.rmtree(created_folder_path)

@pytest.fixture
def complex_cleanup_dependencies_folder():
    yield
    created_folder_path = INSTALL_PROJECT_PATH.joinpath(DEPENDENCIES_FOLDER)
    if os.path.exists(created_folder_path):
        shutil.rmtree(created_folder_path)
