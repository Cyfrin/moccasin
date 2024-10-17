import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from boa_zksync import set_zksync_test_env

from moccasin.commands.wallet import save_to_keystores
from moccasin.config import Config, initialize_global_config
from moccasin.constants.vars import DEPENDENCIES_FOLDER
from tests.conftest import ZKSYNC_PROJECT_PATH

ZK_RICH_KEYSTORE_NAME = "zk-rich1"
ZK_RICH_PRIVATE_KEY = (
    "0x3d3cbc973389cb26f657686445bcc75662b415b656078503592ac8c1abb8810e"
)
ZK_RICH_KEYSTORE_PASSWORD = "password"


# ------------------------------------------------------------------
#                         SESSION SCOPED
# ------------------------------------------------------------------
@pytest.fixture(scope="session")
def zk_rich_keystore(session_monkeypatch, moccasin_home_folder):
    keystore_path = moccasin_home_folder.joinpath("keystores")
    save_to_keystores(
        ZK_RICH_KEYSTORE_NAME,
        ZK_RICH_PRIVATE_KEY,
        password=ZK_RICH_KEYSTORE_PASSWORD,
        keystores_path=Path(keystore_path),
    )
    session_monkeypatch.setenv("MOCCASIN_KEYSTORE_PATH", str(keystore_path))
    session_monkeypatch.setattr(vars, "MOCCASIN_KEYSTORE_PATH", keystore_path)
    with tempfile.NamedTemporaryFile(mode="w") as temp_file:
        temp_file_path = Path(temp_file.name)
        session_monkeypatch.setenv("ZK_RICH1_PASSWORD_FILE", str(temp_file_path))
        temp_file.write(ZK_RICH_KEYSTORE_PASSWORD)
        temp_file.flush()
        yield Path(keystore_path)


# ------------------------------------------------------------------
#                         MODULE SCOPED
# ------------------------------------------------------------------
@pytest.fixture(scope="module")
def zk_temp_path() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(ZKSYNC_PROJECT_PATH, os.path.join(temp_dir), dirs_exist_ok=True)
        yield Path(temp_dir)


@pytest.fixture(scope="module")
def zksync_project_config(zk_temp_path) -> Config:
    return initialize_global_config(zk_temp_path)


@pytest.fixture(scope="module")
def zksync_out_folder(zksync_project_config) -> Config:
    return zksync_project_config.out_folder


# REVIEW: We may not need this anymore?
@pytest.fixture
def zksync_cleanup_coverage(zk_temp_path):
    yield
    coverage_file = zk_temp_path.joinpath(".coverage")
    if os.path.exists(coverage_file):
        os.remove(coverage_file)


@pytest.fixture
def zksync_cleanup_out_folder(zk_temp_path, zksync_out_folder):
    yield
    created_folder_path = zk_temp_path.joinpath(zksync_out_folder)
    if os.path.exists(created_folder_path):
        shutil.rmtree(created_folder_path)


@pytest.fixture
def zksync_cleanup_dependencies_folder(zk_temp_path):
    yield
    created_folder_path = zk_temp_path.joinpath(DEPENDENCIES_FOLDER)
    if os.path.exists(created_folder_path):
        shutil.rmtree(created_folder_path)


@pytest.fixture(scope="module")
def zksync_test_env():
    set_zksync_test_env()
