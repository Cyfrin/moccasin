import os
from pathlib import Path

import pytest

from moccasin.commands.deployments import print_deployments_from_cli
from moccasin.commands.run import run_script
from tests.conftest import DEPLOYMENTS_PROJECT_PATH

MOCK_AGGREGATOR = "MockV3Aggregator"
COUNTER = "Counter"


# ------------------------------------------------------------------
#                      READING DEPLOYMENTS
# ------------------------------------------------------------------
def test_print_deployments_finds_one(capsys, deployments_project_config, anvil_process):
    print_deployments_from_cli(MOCK_AGGREGATOR, network="anvil")
    captured = capsys.readouterr()
    assert MOCK_AGGREGATOR in captured.out
    assert "deployments: 1" in captured.out


def test_print_deployments_finds_two(capsys, deployments_project_config, anvil_process):
    print_deployments_from_cli(COUNTER, network="anvil")
    captured = capsys.readouterr()
    assert COUNTER in captured.out
    assert "deployments: 2" in captured.out


def test_format_level_can_be_above_four(
    capsys, deployments_project_config, anvil_process
):
    print_deployments_from_cli(COUNTER, network="anvil", format_level=100)
    captured = capsys.readouterr()
    assert COUNTER in captured.out
    assert "deployments: 2" in captured.out


def test_limit_drops_deployment_amount(
    capsys, deployments_project_config, anvil_process
):
    print_deployments_from_cli(COUNTER, network="anvil", limit=1)
    captured = capsys.readouterr()
    assert COUNTER in captured.out
    assert "deployments: 1" in captured.out


# ------------------------------------------------------------------
#                READING AND WRITING DEPLOYMENTS
# ------------------------------------------------------------------
def test_records_deployment_on_deployment(deployments_project_config, anvil_process):
    current_dir = Path.cwd()
    starting_deployments_number = 0
    try:
        os.chdir(DEPLOYMENTS_PROJECT_PATH)
        deployments_project_config.set_active_network("anvil")
        active_network = deployments_project_config.get_active_network()
        starting_deployments_number = len(
            active_network.get_deployments_unchecked(COUNTER)
        )
        run_script("deploy", network="anvil")
    finally:
        os.chdir(current_dir)
    assert starting_deployments_number == 2

    active_network = deployments_project_config.get_active_network()
    latest_contract = active_network.get_latest_contract_unchecked(COUNTER)
    deployments = active_network.get_deployments_unchecked(COUNTER)

    # Ending deployments number should be 3
    assert len(deployments) == 3
    assert latest_contract.number() == 1


def test_checks_integrity_of_contracts(
    deployments_project_config, anvil_process, deployments_contract_override
):
    current_dir = Path.cwd()
    starting_deployments_number = 0
    try:
        os.chdir(DEPLOYMENTS_PROJECT_PATH)
        deployments_project_config.set_active_network("anvil")
        active_network = deployments_project_config.get_active_network()
        starting_deployments_number = len(
            active_network.get_deployments_checked(COUNTER)
        )
        run_script("deploy", network="anvil")
    finally:
        os.chdir(current_dir)
    # Since none of the previously deployed contracts have the new code
    assert starting_deployments_number == 0

    latest_contract = active_network.get_latest_contract_checked(COUNTER)
    checked_deployments = active_network.get_deployments_checked(COUNTER)
    unchecked_deployments = active_network.get_deployments_unchecked(COUNTER)

    # Ending deployments number should be 1, since they don't have the same integrity
    assert len(checked_deployments) == 1
    assert len(unchecked_deployments) == 3
    assert latest_contract.number() == 2


def test_local_networks_dont_have_data_saved_to_db(
    deployments_project_config, anvil_process
):
    current_dir = Path.cwd()
    starting_deployments_number = 0
    try:
        os.chdir(DEPLOYMENTS_PROJECT_PATH)
        run_script("deploy")
    finally:
        os.chdir(current_dir)
    assert starting_deployments_number == 0

    active_network = deployments_project_config.get_active_network()

    with pytest.raises(
        ValueError,
        match="The database is either not set, or save_to_db is false for network pyevm.",
    ):
        active_network.get_latest_contract_unchecked(COUNTER)
        active_network.get_deployments_unchecked(COUNTER)
