import os
from pathlib import Path

from moccasin.commands.run import get_script_path, run_script
from tests.constants import COMPLEX_PROJECT_PATH


def test_get_script_path_for_single_name(complex_project_config):
    script_path = get_script_path("deploy")
    assert script_path == complex_project_config.get_root() / "script/deploy.py"


def test_get_script_path_for_relative_path(complex_project_config):
    script_path = get_script_path("./script/deploy.py")
    assert script_path == complex_project_config.get_root() / "script/deploy.py"


def test_get_script_path_for_absolute_path(complex_temp_path, complex_project_config):
    script_path = get_script_path(complex_temp_path.joinpath("./script/deploy.py"))
    assert script_path == complex_project_config.get_root() / "script/deploy.py"


def test_get_script_path_respects_configured_script_folder(monkeypatch, tmp_path):
    # A project may override the script folder (e.g. `script = "scripts"`); `mox run`
    # must resolve scripts under the configured folder, not the hardcoded default.
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "deploy.py").write_text("")

    class _Config:
        script_folder = "scripts"

        def get_root(self):
            return tmp_path

    monkeypatch.setattr("moccasin.commands.run.get_config", lambda: _Config())
    assert get_script_path("deploy") == tmp_path / "scripts" / "deploy.py"
    # a relative path that already includes the configured folder is used as-is
    assert get_script_path("scripts/deploy.py") == tmp_path / "scripts" / "deploy.py"


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
