from gaboon.commands.run import get_script_path
from tests.conftest import COMPLEX_PROJECT_PATH


def test_get_script_path_for_single_name(complex_project_config):
    script_path = get_script_path("deploy")
    assert script_path == complex_project_config.get_root() / "script/deploy.py"


def test_get_script_path_for_relative_path(complex_project_config):
    script_path = get_script_path("./script/deploy.py")
    assert script_path == complex_project_config.get_root() / "script/deploy.py"


def test_get_script_path_for_absolute_path(complex_project_config):
    script_path = get_script_path(COMPLEX_PROJECT_PATH.joinpath("./script/deploy.py"))
    assert script_path == complex_project_config.get_root() / "script/deploy.py"
