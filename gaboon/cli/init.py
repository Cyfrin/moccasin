from pathlib import Path
from typing import Any, List
from gaboon.utils.cli_constants import (
    PROJECT_FOLDERS,
    GITIGNORE,
    GITATTRIBUTES,
    PROJECT_FILES,
)
from docopt import docopt

__doc__ = """Usage: gaboon init [<path>] [options]

Arguments:
    <path>                Path to initialize (default is the current path)

Options:
  --force -f            Allow initialization inside a directory that is not
                        empty, or a subdirectory of an existing project
  --help -h             Display this message
"""


def main() -> int:
    args = docopt(__doc__)
    path: str = new_project(args["<path>"] or ".", args["--force"])
    print(f"Project initialized at {path}")
    return 0


def new_project(project_path_str: str = ".", force: bool = False) -> str:
    """Initializes a new project.

    Args:
        project_path: Path to initialize the project at. If not exists, it will be created.
        force: If True, it will create folders and files even if the folder is not empty.

    Returns the path to the project as a string.
    """
    project_path = Path(project_path_str).resolve()
    if not force and project_path.exists() and list(project_path.glob("*")):
        raise FileExistsError(f"Directory is not empty: {project_path}")
    project_path.mkdir(exist_ok=True)
    _create_folders(project_path)
    _create_files(project_path)
    return str(project_path)


def _create_folders(project_path: Path) -> None:
    for folder in PROJECT_FOLDERS:
        Path(project_path).joinpath(folder).mkdir(exist_ok=True)


def _create_files(project_path: Path) -> None:
    gitignore = project_path.joinpath(".gitignore")
    if not gitignore.exists():
        with gitignore.open("w") as fp:
            fp.write(GITIGNORE)
    gitattributes = project_path.joinpath(".gitattributes")
    if not gitattributes.exists():
        with gitattributes.open("w") as fp:
            fp.write(GITATTRIBUTES)
    for file in PROJECT_FILES:
        Path(project_path).joinpath(file).touch()
