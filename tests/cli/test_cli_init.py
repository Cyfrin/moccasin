import subprocess
import tempfile
from pathlib import Path

from moccasin.config import Config
from moccasin.constants.file_data import GITATTRIBUTES, GITIGNORE
from moccasin.constants.vars import DEFAULT_PROJECT_FOLDERS

EXPECTED_HELP_TEXT = "Pythonic Smart Contract Development Framework"


def test_init(mox_path):
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run(
            [mox_path, "init", Path(temp_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        _assert_files_and_folders_exist(Path(temp_dir))
        _assert_files_and_folders_exist(Path(temp_dir))
        assert result.returncode == 0


def test_find_project_root_from_new_project(mox_path):
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run(
            [mox_path, "init", Path(temp_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        project_root: Path = Config.find_project_root(Path(temp_dir))
        assert project_root.resolve() == Path(temp_dir).resolve()
        assert result.returncode == 0


def _assert_files_and_folders_exist(temp_dir: Path):
    for folder in DEFAULT_PROJECT_FOLDERS:
        assert temp_dir.joinpath(folder).exists()
    assert temp_dir.joinpath("README.md").exists()
    assert temp_dir.joinpath("moccasin.toml").exists()
    assert temp_dir.joinpath(".coveragerc").exists()
    assert temp_dir.joinpath(Path(".gitignore")).exists()
    assert temp_dir.joinpath(Path(".gitattributes")).exists()
    with temp_dir.joinpath(Path(".gitignore")).open() as fp:
        assert fp.read() == GITIGNORE
    with temp_dir.joinpath(Path(".gitattributes")).open() as fp:
        assert fp.read() == GITATTRIBUTES
