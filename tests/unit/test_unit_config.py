import os
import tempfile
from pathlib import Path

import boa

from moccasin.config import Config, get_config


# REVIEW: I guess this is cool? You can setup a project without a `moccasin.toml` file? Maybe this is a bug?
# It'll just use the default network data like pyevm and eravm...
def test_networks_initialized():
    with tempfile.TemporaryDirectory() as temp_dir:
        config = Config(Path(temp_dir))
        assert config.get_networks() is not None


def test_set_dot_env(complex_project_config):
    config = get_config()
    assert config.dot_env == ".hello"
    assert os.getenv("HELLO_THERE") == "HI"


def test_active_boa(complex_project_config):
    config = get_config()
    network = "anvil"
    config.set_active_network(network, activate_boa=False)
    # The env hasn't updated yet
    assert boa.env.nickname == "pyevm"
