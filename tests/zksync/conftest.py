import os
import shutil

import pytest
from boa_zksync import set_zksync_test_env

from moccasin.config import Config, initialize_global_config
from moccasin.constants.vars import DEPENDENCIES_FOLDER
from tests.conftest import ZKSYNC_PROJECT_PATH


## ZKSync Fixtures
@pytest.fixture(scope="session")
def zksync_project_config() -> Config:
    return initialize_global_config(ZKSYNC_PROJECT_PATH)


@pytest.fixture(scope="session")
def zksync_out_folder(zksync_project_config) -> Config:
    return zksync_project_config.out_folder


@pytest.fixture
def zksync_cleanup_coverage():
    yield
    coverage_file = ZKSYNC_PROJECT_PATH.joinpath(".coverage")
    if os.path.exists(coverage_file):
        os.remove(coverage_file)


@pytest.fixture
def zksync_cleanup_out_folder(zksync_out_folder):
    yield
    created_folder_path = ZKSYNC_PROJECT_PATH.joinpath(zksync_out_folder)
    if os.path.exists(created_folder_path):
        shutil.rmtree(created_folder_path)


@pytest.fixture
def zksync_cleanup_dependencies_folder():
    yield
    created_folder_path = ZKSYNC_PROJECT_PATH.joinpath(DEPENDENCIES_FOLDER)
    if os.path.exists(created_folder_path):
        shutil.rmtree(created_folder_path)


@pytest.fixture(scope="module")
def zksync_test_env():
    set_zksync_test_env()
