from moccasin.commands.deployments import print_deployments_from_cli

import pytest

MOCK_AGGREGATOR = "MockV3Aggregator"
COUNTER = "Counter"


# ------------------------------------------------------------------
#                      READING DEPLOYMENTS
# ------------------------------------------------------------------
@pytest.mark.ignore_isolation
def test_print_deployments_finds_one(
    capsys, deployments_database, deployments_project_config_read, anvil_process
):
    print_deployments_from_cli(MOCK_AGGREGATOR, network="anvil")
    captured = capsys.readouterr()
    assert MOCK_AGGREGATOR in captured.out
    assert "deployments: 1" in captured.out


@pytest.mark.ignore_isolation
def test_print_deployments_finds_two(
    capsys, deployments_database, deployments_project_config_read, anvil_process
):
    print_deployments_from_cli(COUNTER, network="anvil")
    captured = capsys.readouterr()
    assert COUNTER in captured.out
    assert "deployments: 2" in captured.out


@pytest.mark.ignore_isolation
def test_format_level_can_be_above_four(
    capsys, deployments_database, deployments_project_config_read, anvil_process
):
    print_deployments_from_cli(COUNTER, network="anvil", format_level=100)
    captured = capsys.readouterr()
    assert COUNTER in captured.out
    assert "deployments: 2" in captured.out


@pytest.mark.ignore_isolation
def test_limit_drops_deployment_amount(
    capsys, deployments_database, deployments_project_config_read, anvil_process
):
    print_deployments_from_cli(COUNTER, network="anvil", limit=1)
    captured = capsys.readouterr()
    assert COUNTER in captured.out
    assert "deployments: 1" in captured.out
