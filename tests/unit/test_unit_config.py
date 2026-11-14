import os
import shutil
import tempfile
import tomllib
from pathlib import Path

import boa

from moccasin.config import Config
from tests.constants import COMPLEX_PROJECT_PATH, NO_CONFIG_PROJECT_PATH


# REVIEW: I guess this is cool? You can setup a project without a `moccasin.toml` file? Maybe this is a bug?
# It'll just use the default network data like pyevm and eravm...
def test_networks_initialized():
    with tempfile.TemporaryDirectory() as temp_dir:
        config = Config(Path(temp_dir))
        assert config.get_networks() is not None


def test_set_dot_env(complex_project_config):
    assert complex_project_config.dot_env == ".hello"
    assert os.getenv("HELLO_THERE") == "HI"


def test_active_boa(complex_project_config):
    network = "anvil"
    complex_project_config.set_active_network(network, activate_boa=False)
    # The env hasn't updated yet
    assert boa.env.nickname == "pyevm"


def test_get_named_contracts(complex_project_config):
    active_network = complex_project_config.get_active_network()
    named_contracts = active_network.get_named_contracts()
    assert isinstance(named_contracts, dict)
    assert named_contracts["price_feed"] is not None


def test_live_or_staging_defaults_to_true(complex_project_config):
    complex_project_config.set_active_network("anvil", activate_boa=False)
    active_network = complex_project_config.get_active_network()
    assert active_network.live_or_staging is True


def test_live_or_staging_is_false_for_local(complex_project_config):
    complex_project_config.set_active_network("pyevm", activate_boa=False)
    active_network = complex_project_config.get_active_network()
    assert active_network.live_or_staging is False


def test_live_or_staging_is_false_for_fork(complex_project_config):
    complex_project_config.set_active_network("fake_chain", activate_boa=False)
    active_network = complex_project_config.get_active_network()
    assert active_network.live_or_staging is False


def test_pyproject_config_overriden_by_moccasin(complex_project_config):
    assert complex_project_config.src_folder == "contracts"


def test_pyproject_can_pull_in_config(complex_project_config):
    silly_network = complex_project_config.networks.get_network("silly_network")
    assert silly_network.name == "silly_network"
    assert silly_network.chain_id == 7777


def test_no_moccasin_toml_paths_exist(no_config_config):
    assert no_config_config.config_path.exists() is False
    assert no_config_config.pyproject_path.exists() is True
    assert no_config_config.dot_env == ".hello"


def test_no_moccasin_toml_can_set_network(no_config_config):
    no_config_config.set_active_network("pyevm")
    active_network = no_config_config.get_active_network()
    assert active_network.name == "pyevm"


def test_write_dependencies_does_not_leak_pyproject_into_moccasin_toml():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        shutil.copytree(COMPLEX_PROJECT_PATH, temp_path, dirs_exist_ok=True)
        pyproject_before = (temp_path / "pyproject.toml").read_text()

        config = Config(temp_path)
        new_deps = ["snekmate==0.1.1", "pcaversaccio/snekmate@2.5.0"]
        config.write_dependencies(new_deps)

        moccasin_text = (temp_path / "moccasin.toml").read_text()
        moccasin_data = tomllib.loads(moccasin_text)

        assert "# The default is true for non-local networks" in moccasin_text
        assert moccasin_data["project"]["dependencies"] == new_deps
        assert moccasin_data["project"]["src"] == "contracts"
        assert "silly_network" not in moccasin_data.get("networks", {})
        assert "pyproject_contract" not in moccasin_data.get("networks", {}).get(
            "contracts", {}
        )
        assert "tool" not in moccasin_data
        assert (temp_path / "pyproject.toml").read_text() == pyproject_before


def test_write_dependencies_empty_moccasin_toml_does_not_copy_pyproject():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        shutil.copy2(COMPLEX_PROJECT_PATH / "pyproject.toml", temp_path / "pyproject.toml")
        (temp_path / "moccasin.toml").write_text("# Keep moccasin comment\n")

        config = Config(temp_path)
        config.write_dependencies(["pcaversaccio/snekmate@2.5.0"])

        moccasin_text = (temp_path / "moccasin.toml").read_text()
        moccasin_data = tomllib.loads(moccasin_text)

        assert "# Keep moccasin comment" in moccasin_text
        assert moccasin_data == {
            "project": {"dependencies": ["pcaversaccio/snekmate@2.5.0"]}
        }
        assert "tool" not in moccasin_data


def test_write_dependencies_pyproject_only_preserves_pyproject_comments():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        shutil.copytree(NO_CONFIG_PROJECT_PATH, temp_path, dirs_exist_ok=True)
        pyproject_file = temp_path / "pyproject.toml"
        pyproject_file.write_text("# Keep pyproject comment\n" + pyproject_file.read_text())

        config = Config(temp_path)
        config.write_dependencies(["pcaversaccio/snekmate@2.5.0"])

        assert not (temp_path / "moccasin.toml").exists()
        pyproject_text = pyproject_file.read_text()
        pyproject_data = tomllib.loads(pyproject_text)

        assert "# Keep pyproject comment" in pyproject_text
        assert (
            pyproject_data["tool"]["moccasin"]["project"]["dependencies"]
            == ["pcaversaccio/snekmate@2.5.0"]
        )
        assert "project" in pyproject_data
