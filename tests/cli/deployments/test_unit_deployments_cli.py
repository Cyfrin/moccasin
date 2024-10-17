from pathlib import Path

from boa.deployments import DeploymentsDB

from moccasin.config import Config


def test_generate_sql_from_args_with_where(blank_tempdir):
    # Arrange
    db_path = blank_tempdir + "/.deployments.db"
    db = DeploymentsDB(db_path)
    contract_name = "MockV3Aggregator"
    chain_id = 31337
    limit = 1

    config = Config(Path("."))
    # This should be a blank pyevm network
    active_network = config.get_active_network()

    # Act
    sql_query, params = active_network._generate_sql_from_args(
        contract_name=contract_name, chain_id=chain_id, limit=limit, db=db
    )
    expected_sql = "SELECT contract_address,contract_name,rpc,deployer,tx_hash,broadcast_ts,tx_dict,receipt_dict,source_code,abi,session_id,deployment_id FROM deployments WHERE contract_name = ? AND json_extract(tx_dict, '$.chainId') = ? ORDER BY broadcast_ts DESC LIMIT ? "
    expected_parametrs = ("MockV3Aggregator", "31337", 1)

    # Assert
    assert sql_query == expected_sql
    assert params == expected_parametrs


def test_generate_sql_from_args_without_where(blank_tempdir):
    # Arrange
    db_path = blank_tempdir + "/.deployments.db"
    db = DeploymentsDB(db_path)
    config = Config(Path("."))
    # This should be a blank pyevm network
    active_network = config.get_active_network()

    # Act
    sql_query, params = active_network._generate_sql_from_args(db=db)
    expected_sql = "SELECT contract_address,contract_name,rpc,deployer,tx_hash,broadcast_ts,tx_dict,receipt_dict,source_code,abi,session_id,deployment_id FROM deployments ORDER BY broadcast_ts DESC "
    expected_parametrs = ()

    # Assert
    assert sql_query == expected_sql
    assert params == expected_parametrs


def test_generate_sql_from_args_without_and(blank_tempdir):
    # Arrange
    db_path = blank_tempdir + "/.deployments.db"
    db = DeploymentsDB(db_path)
    contract_name = "MockV3Aggregator"
    limit = 1
    config = Config(Path("."))
    # This should be a blank pyevm network
    active_network = config.get_active_network()

    # Act
    sql_query, params = active_network._generate_sql_from_args(
        contract_name=contract_name, limit=limit, db=db
    )
    expected_sql = "SELECT contract_address,contract_name,rpc,deployer,tx_hash,broadcast_ts,tx_dict,receipt_dict,source_code,abi,session_id,deployment_id FROM deployments WHERE contract_name = ? ORDER BY broadcast_ts DESC LIMIT ? "
    expected_parametrs = ("MockV3Aggregator", 1)

    # Assert
    assert sql_query == expected_sql
    assert params == expected_parametrs
