from pathlib import Path
import shutil
from typing import Generator
import pytest
from moccasin.config import Config, _set_global_config
import os
from boa.deployments import DeploymentsDB, set_deployments_db

DEPLOYMENTS_PROJECT_PATH = Path(__file__).parent.parent.joinpath(
    "data/deployments_project/"
)


# ------------------------------------------------------------------
#                      DEPLOYMENTS PROJECT FIXTURES
# ------------------------------------------------------------------
@pytest.fixture(scope="module")
def deployments_project_config_read() -> Generator[Config, None, None]:
    """We need to copy the starting database to a test database before running the tests.

    And then, initialize the config file from the moccasin.toml

    At the end, we should reset the test database to the starting database.

    Note, this is for reading only, we should reset the DB as done in the write tests below.
    """
    starting_db_path = os.path.join(
        DEPLOYMENTS_PROJECT_PATH, ".starting_deployments.db"
    )
    test_db_path = os.path.join(DEPLOYMENTS_PROJECT_PATH, ".deployments.db")

    if not os.path.exists(starting_db_path):
        raise FileNotFoundError(f"Starting database not found: {starting_db_path}")
    shutil.copy2(starting_db_path, test_db_path)

    config = _set_global_config(DEPLOYMENTS_PROJECT_PATH)

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


@pytest.fixture(scope="module")
def deployments_project_config_write() -> Config:
    config = _set_global_config(DEPLOYMENTS_PROJECT_PATH)
    return config


# So that each deployment test can start from a fresh DB
@pytest.fixture
def deployments_database(deployments_project_config_write):
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

    # We have to reset the DB between tests
    db = DeploymentsDB(deployments_project_config_write.get_active_network().db_path)
    set_deployments_db(db)

    yield

    if os.path.exists(test_db_path):
        os.remove(test_db_path)
