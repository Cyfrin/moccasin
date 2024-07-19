from pathlib import Path

from gaboon.utils._cli_constants import (
    GITATTRIBUTES,
    GITIGNORE,
    PROJECT_FILES,
    PROJECT_FOLDERS,
)

COUNTER_PROJECT_FILE_PATH = Path(__file__).parent.joinpath(
    "test_projects/gaboon_project/src/Counter.vy"
)


def assert_files_and_folders_exist(temp_dir: Path):
    for folder in PROJECT_FOLDERS:
        assert temp_dir.joinpath(folder).exists()
    for file in PROJECT_FILES:
        assert temp_dir.joinpath(file).exists()
    # assert the temp_dir dir has the .gitignore and .gitattributes
    assert temp_dir.joinpath(Path(".gitignore")).exists()
    assert temp_dir.joinpath(Path(".gitattributes")).exists()
    # assert the content of the .gitignore and .gitattributes
    with temp_dir.joinpath(Path(".gitignore")).open() as fp:
        assert fp.read() == GITIGNORE
    with temp_dir.joinpath(Path(".gitattributes")).open() as fp:
        assert fp.read() == GITATTRIBUTES
