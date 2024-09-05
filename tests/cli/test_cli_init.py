import subprocess
import tempfile
from pathlib import Path
from gaboon.config import Config
from gaboon.constants.vars import DEFAULT_PROJECT_FOLDERS
from gaboon.constants.file_data import GITIGNORE, GITATTRIBUTES

EXPECTED_HELP_TEXT = "Pythonic Smart Contract Development Framework"


def test_init(gab_path):
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run(
            [gab_path, "init", Path(temp_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        _assert_files_and_folders_exist(Path(temp_dir))
        _assert_files_and_folders_exist(Path(temp_dir))
        assert result.returncode == 0


def test_find_project_root_from_new_project(gab_path):
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run(
            [gab_path, "init", Path(temp_dir)],
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
    assert temp_dir.joinpath("gaboon.toml").exists()
    assert temp_dir.joinpath(Path(".gitignore")).exists()
    assert temp_dir.joinpath(Path(".gitattributes")).exists()
    with temp_dir.joinpath(Path(".gitignore")).open() as fp:
        assert fp.read() == GITIGNORE
    with temp_dir.joinpath(Path(".gitattributes")).open() as fp:
        assert fp.read() == GITATTRIBUTES
