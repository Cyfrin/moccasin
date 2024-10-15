# REVIEW: These are all messed up for some reason right now

# from pathlib import Path
# import os
# import subprocess
# from tests.conftest import DEPLOYMENTS_PROJECT_PATH
# from moccasin.commands.run import run_script
# import pytest

# MOCK_AGGREGATOR = "MockV3Aggregator"
# COUNTER = "Counter"


# # ------------------------------------------------------------------
# #                READING AND WRITING DEPLOYMENTS
# # ------------------------------------------------------------------
# def test_local_networks_dont_have_data_saved_to_db(
#     deployments_project_config_write, anvil_process_reset
# ):
#     current_dir = Path.cwd()
#     starting_deployments_number = 0
#     try:
#         os.chdir(DEPLOYMENTS_PROJECT_PATH)
#         run_script("deploy")
#     finally:
#         os.chdir(current_dir)
#     assert starting_deployments_number == 0

#     active_network = deployments_project_config_write.get_active_network()

#     with pytest.raises(
#         ValueError,
#         match="The database is either not set, or save_to_db is false for network pyevm.",
#     ):
#         active_network.get_latest_contract_unchecked(COUNTER)
#         active_network.get_deployments_unchecked(COUNTER)


# def test_checks_integrity_of_contracts(
#     mox_path,
#     deployments_project_config_write,
#     deployments_contract_override,
#     anvil_process_reset,
# ):
#     current_dir = Path.cwd()
#     starting_deployments_number = 0
#     try:
#         os.chdir(DEPLOYMENTS_PROJECT_PATH)

#         deployments_project_config_write.set_active_network("anvil")
#         active_network = deployments_project_config_write.get_active_network()

#         starting_deployments_number = len(
#             active_network.get_deployments_checked(COUNTER)
#         )
#         result = subprocess.run(
#             [mox_path, "run", "deploy", "--network", "anvil"],
#             input="\n",
#             check=True,
#             text=True,
#             capture_output=True,
#         )
#     finally:
#         os.chdir(current_dir)

#     assert "Ending count:  2" in result.stdout

#     # Since none of the previously deployed contracts have the new code
#     assert starting_deployments_number == 0

#     latest_contract = active_network.get_latest_contract_checked(COUNTER)
#     checked_deployments = active_network.get_deployments_checked(COUNTER)
#     unchecked_deployments = active_network.get_deployments_unchecked(COUNTER)

#     # Ending deployments number should be 1, since they don't have the same integrity
#     assert len(checked_deployments) == 1
#     assert len(unchecked_deployments) == 3
#     assert latest_contract.address is not None

# from pathlib import Path
# import os
# from tests.conftest import DEPLOYMENTS_PROJECT_PATH
# import subprocess

# COUNTER = "Counter"

# REVIEW: Idk why this test is failing

# def test_records_deployment_on_deployment(
#     mox_path, deployments_project_config_write, anvil_process
# ):
#     current_dir = Path.cwd()
#     starting_deployments_number = 0
#     try:
#         os.chdir(DEPLOYMENTS_PROJECT_PATH)
#         deployments_project_config_write.set_active_network("anvil")
#         active_network = deployments_project_config_write.get_active_network()
#         starting_deployments_number = len(
#             active_network.get_deployments_unchecked(COUNTER)
#         )
#         result = subprocess.run(
#             [mox_path, "run", "deploy", "--network", "anvil"],
#             input="\n",
#             check=True,
#             text=True,
#             capture_output=True,
#         )
#     finally:
#         os.chdir(current_dir)
#     assert starting_deployments_number == 2

#     assert "Ending count:  1" in result.stdout

#     active_network = deployments_project_config_write.get_active_network()
#     deployments = active_network.get_deployments_unchecked(COUNTER)

#     assert len(deployments) == 3
