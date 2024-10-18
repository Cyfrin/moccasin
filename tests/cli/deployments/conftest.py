import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator

import pytest

from moccasin.config import Config, _set_global_config

DEPLOYMENTS_PROJECT_PATH = Path(__file__).parent.parent.parent.joinpath(
    "data/deployments_project/"
)


# ------------------------------------------------------------------
#                      DEPLOYMENTS PROJECT FIXTURES
# ------------------------------------------------------------------
@pytest.fixture(scope="function")
def deployments_path() -> Generator[Path, None, None]:
    """
    Create a fresh copy of the entire project directory for each deployment test.
    Initialize the config file from moccasin.toml.
    """
    starting_dir = Path.cwd()

    with TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)

        # Copy the entire project directory to the temporary directory
        temp_project_path = Path(temp_dir) / "project"
        shutil.copytree(DEPLOYMENTS_PROJECT_PATH, temp_project_path)

        # Update paths
        starting_db_path = temp_project_path / ".starting_deployments.db"
        test_db_path = temp_project_path / ".deployments.db"

        if not starting_db_path.exists():
            raise FileNotFoundError(f"Starting database not found: {starting_db_path}")

        # Copy the starting database to the test database
        shutil.copy2(starting_db_path, test_db_path)
        yield temp_project_path

    os.chdir(starting_dir)


@pytest.fixture(scope="function")
def deployments_config(deployments_path) -> Config:
    config = _set_global_config(deployments_path)
    config.set_active_network("pyevm", activate_boa=False)
    return config


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
def deployments_contract_override(deployments_path):
    counter_contract = deployments_path.joinpath("src/Counter.vy")
    with open(counter_contract, "w") as f:
        f.write(COUNTER_CONTRACT_OVERRIDE)
    return


@pytest.fixture(scope="module")
def blank_tempdir():
    original_dir = Path.cwd()
    with TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        yield temp_dir
    os.chdir(original_dir)
