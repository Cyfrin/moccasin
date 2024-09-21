import os

from moccasin.config import get_config


def test_set_dot_env(complex_project_config):
    config = get_config()
    assert config.dot_env == ".hello"
    assert os.getenv("HELLO_THERE") == "HI"
