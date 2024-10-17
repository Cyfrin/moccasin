import os
from pathlib import Path

from moccasin.commands.run import get_script_path, run_script
from tests.conftest import COMPLEX_PROJECT_PATH


def test_get_script_path_for_single_name(complex_project_config):
    script_path = get_script_path("deploy")
    assert script_path == complex_project_config.get_root() / "script/deploy.py"


def test_get_script_path_for_relative_path(complex_project_config):
    script_path = get_script_path("./script/deploy.py")
    assert script_path == complex_project_config.get_root() / "script/deploy.py"


def test_get_script_path_for_absolute_path(complex_temp_path, complex_project_config):
    script_path = get_script_path(complex_temp_path.joinpath("./script/deploy.py"))
    assert script_path == complex_project_config.get_root() / "script/deploy.py"


def test_no_prompt_on_test_networks(complex_project_config, capsys):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        run_script("deploy", network="pyevm")
    finally:
        os.chdir(current_dir)
    captured = capsys.readouterr()
    assert "Starting count:  0" in captured.out
    assert "Ending count:  1" in captured.out
