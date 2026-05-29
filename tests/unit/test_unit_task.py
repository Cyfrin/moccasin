import logging
import subprocess
from argparse import Namespace
from unittest.mock import MagicMock, patch

from moccasin.commands.task import main as task_main
from moccasin.config import _set_global_config

TITANOBOA_LOGGER = "titanoboa"


def _make_args(name=None, list_only=False, forward_args=None):
    ns = Namespace()
    ns.name = name
    ns.list = list_only
    ns.forward_args = forward_args if forward_args is not None else []
    return ns


def _ensure_complex_scripts_config(complex_temp_path):
    """Re-bind the global Config to the complex_project fixture.

    Module-scoped fixtures cache their Config object but other fixtures
    may overwrite the global config in between tests; rebinding ensures
    ``task.main`` sees the complex_project ``[scripts]`` table.
    """
    return _set_global_config(complex_temp_path)


def test_task_list_prints_all_scripts(complex_temp_path, caplog):
    _ensure_complex_scripts_config(complex_temp_path)
    with caplog.at_level(logging.INFO, logger=TITANOBOA_LOGGER):
        rc = task_main(_make_args(list_only=True))
    assert rc == 0
    assert "hello" in caplog.text
    assert "test-unit" in caplog.text


def test_task_runs_named_command(complex_temp_path):
    _ensure_complex_scripts_config(complex_temp_path)
    with patch("moccasin.commands.task.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        rc = task_main(_make_args(name="hello"))
    assert rc == 0
    mock_run.assert_called_once()
    cmd_arg = mock_run.call_args.args[0]
    assert cmd_arg == "echo hi from mox task"
    assert mock_run.call_args.kwargs.get("shell") is True


def test_task_unknown_name_exits_nonzero(complex_temp_path, caplog):
    _ensure_complex_scripts_config(complex_temp_path)
    with caplog.at_level(logging.ERROR, logger=TITANOBOA_LOGGER):
        rc = task_main(_make_args(name="does-not-exist"))
    assert rc == 1
    assert "Unknown script" in caplog.text


def test_task_forwards_extra_args(complex_temp_path):
    _ensure_complex_scripts_config(complex_temp_path)
    with patch("moccasin.commands.task.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        rc = task_main(
            _make_args(name="test-unit", forward_args=["-k", "test_mint"])
        )
    assert rc == 0
    cmd_arg = mock_run.call_args.args[0]
    assert cmd_arg.startswith("mox test tests/unit")
    assert "-k" in cmd_arg
    assert "test_mint" in cmd_arg


def test_task_propagates_nonzero_exit_code(complex_temp_path):
    _ensure_complex_scripts_config(complex_temp_path)
    with patch("moccasin.commands.task.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=2)
        rc = task_main(_make_args(name="hello"))
    assert rc == 2


def test_task_no_scripts_section_lists_empty(no_config_config, caplog):
    with caplog.at_level(logging.INFO, logger=TITANOBOA_LOGGER):
        rc = task_main(_make_args(list_only=True))
    assert rc == 0
    assert "No scripts defined." in caplog.text


def test_task_alias_t_works(mox_path):
    """The 't' alias should resolve to the 'task' command."""
    result = subprocess.run(
        [mox_path, "t", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "[scripts]" in result.stdout


def test_config_exposes_scripts_attribute(complex_temp_path):
    config = _set_global_config(complex_temp_path)
    assert config.scripts == {
        "hello": "echo hi from mox task",
        "test-unit": "mox test tests/unit",
    }
    assert config.get_scripts() == config.scripts
