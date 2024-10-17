from moccasin.commands.deployments import print_deployments_from_cli

MOCK_AGGREGATOR = "MockV3Aggregator"
COUNTER = "Counter"


# ------------------------------------------------------------------
#                      READING DEPLOYMENTS
# ------------------------------------------------------------------
def test_print_deployments_finds_one(
    capsys, deployments_path, deployments_config, anvil_process
):
    print_deployments_from_cli(MOCK_AGGREGATOR, network="anvil")
    captured = capsys.readouterr()
    assert MOCK_AGGREGATOR in captured.out
    assert "deployments: 1" in captured.out


def test_print_deployments_finds_two(
    capsys, deployments_path, deployments_config, anvil_process
):
    print_deployments_from_cli(COUNTER, network="anvil")
    captured = capsys.readouterr()
    assert COUNTER in captured.out
    assert "deployments: 2" in captured.out


def test_format_level_can_be_above_four(
    capsys, deployments_path, deployments_config, anvil_process
):
    print_deployments_from_cli(COUNTER, network="anvil", format_level=100)
    captured = capsys.readouterr()
    assert COUNTER in captured.out
    assert "deployments: 2" in captured.out


def test_limit_drops_deployment_amount(
    capsys, deployments_path, deployments_config, anvil_process
):
    print_deployments_from_cli(COUNTER, network="anvil", limit=1)
    captured = capsys.readouterr()
    assert COUNTER in captured.out
    assert "deployments: 1" in captured.out
