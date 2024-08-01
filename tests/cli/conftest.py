from pathlib import Path
import pytest
import os
import sys
import shutil
from gaboon.constants.vars import BUILD_FOLDER
import gaboon.constants.vars as vars
from gaboon.commands.wallet import save_to_keystores
import tempfile

COMPLEX_PROJECT_PATH = Path(__file__).parent.parent.joinpath("data/complex_project/")
ANVIL1_PRIVATE_KEY = (
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
)
ANVIL1_KEYSTORE_NAME = "anvil1"
ANVIL1_KEYSTORE_PASSWORD = "password"


@pytest.fixture
def gab_path():
    return os.path.join(os.path.dirname(sys.executable), "gab")


@pytest.fixture
def cleanup_out_folder():
    yield
    created_folder_path = COMPLEX_PROJECT_PATH.joinpath(BUILD_FOLDER)
    if os.path.exists(created_folder_path):
        shutil.rmtree(created_folder_path)


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
        yield
