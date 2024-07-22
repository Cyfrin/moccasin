import tempfile
from pathlib import Path
from gaboon.cli.init import new_project
from gaboon.utils._cli_constants import (
    PROJECT_FOLDERS,
    GITIGNORE,
    GITATTRIBUTES,
)
from tests.base_test import assert_files_and_folders_exist


def test_cli_init():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        new_project(project_path_str=temp_dir)
        assert_files_and_folders_exist(temp_dir)
        for folder in PROJECT_FOLDERS:
            assert temp_dir.joinpath(folder).exists()
        # assert the temp_dir dir has the .gitignore and .gitattributes
        assert temp_dir.joinpath(Path(".gitignore")).exists()
        assert temp_dir.joinpath(Path(".gitattributes")).exists()
        # assert the content of the .gitignore and .gitattributes
        with temp_dir.joinpath(Path(".gitignore")).open() as fp:
            assert fp.read() == GITIGNORE
        with temp_dir.joinpath(Path(".gitattributes")).open() as fp:
            assert fp.read() == GITATTRIBUTES
