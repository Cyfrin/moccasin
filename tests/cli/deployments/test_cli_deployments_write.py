import os
import subprocess
import warnings
from pathlib import Path

from moccasin.commands.run import run_script

MOCK_AGGREGATOR = "MockV3Aggregator"
COUNTER = "Counter"


# ------------------------------------------------------------------
#                READING AND WRITING DEPLOYMENTS
# ------------------------------------------------------------------
def test_local_networks_dont_have_data_saved_to_db(
    deployments_config, deployments_path, anvil
):
    current_dir = Path.cwd()
    starting_deployments_number = 0
    try:
        os.chdir(deployments_path)
        run_script("deploy")
    finally:
        os.chdir(current_dir)
    assert starting_deployments_number == 0

    active_network = deployments_config.get_active_network()

    active_network.get_latest_contract_unchecked(COUNTER)
    active_network.get_deployments_unchecked(COUNTER)


def test_checks_integrity_of_contracts(
    mox_path, deployments_config, deployments_path, deployments_contract_override, anvil
):
    current_dir = Path.cwd()
    try:
        os.chdir(deployments_path)
        deployments_config.set_active_network("anvil", activate_boa=False)
        active_network = deployments_config.get_active_network()
        anvil_chain_id = 31337

        starting_deployments_number_checked = len(
            active_network.get_deployments_checked(
                contract_name=COUNTER, limit=None, chain_id=anvil_chain_id
            )
        )
        starting_deployments_number_unchecked = len(
            active_network.get_deployments_unchecked(
                contract_name=COUNTER, limit=None, chain_id=anvil_chain_id
            )
        )

        result = subprocess.run(
            [mox_path, "run", "deploy", "--network", "anvil"],
            check=True,
            text=True,
            capture_output=True,
        )
    finally:
        os.chdir(current_dir)

    assert "Ending count:  2" in result.stdout
    assert starting_deployments_number_unchecked == 2
    assert starting_deployments_number_checked == 0

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", message="Requested .* but there is no bytecode at that address!"
        )
        latest_contract = active_network.get_latest_contract_checked(
            contract_name=COUNTER
        )
    checked_deployments = active_network.get_deployments_checked(contract_name=COUNTER)
    unchecked_deployments = active_network.get_deployments_unchecked(
        contract_name=COUNTER
    )

    # Ending deployments number should be 1, since they don't have the same integrity
    assert len(checked_deployments) == 1
    assert len(unchecked_deployments) == 3
    assert latest_contract.address is not None


def test_records_deployment_on_deployment(
    mox_path, deployments_config, deployments_path, anvil
):
    current_dir = Path.cwd()
    starting_deployments_number = 0
    try:
        os.chdir(deployments_path)
        deployments_config.set_active_network("anvil", activate_boa=False)
        active_network = deployments_config.get_active_network()
        starting_deployments_number = len(
            active_network.get_deployments_unchecked(contract_name=COUNTER)
        )
        result = subprocess.run(
            [mox_path, "run", "deploy", "--network", "anvil"],
            check=True,
            text=True,
            capture_output=True,
        )
    finally:
        os.chdir(current_dir)
    assert starting_deployments_number == 2

    assert "Ending count:  1" in result.stdout

    active_network = deployments_config.get_active_network()
    deployments = active_network.get_deployments_unchecked(COUNTER)

    assert len(deployments) == 3
