from pathlib import Path
from gaboon.utils._cli_constants import (
    PROJECT_FOLDERS,
    GITIGNORE,
    GITATTRIBUTES,
    PROJECT_FILES,
    COUNTER_CONTRACT_PATH,
    COUNTER_VYPER_CONTRACT_SRC,
)
from docopt import ParsedOptions, docopt

__doc__ = """Usage: gab init [<path>] [options]

Arguments:
    <path>                Path to initialize (default is the current path)

Options:
  --force -f            Allow initialization inside a directory that is not
                        empty, or a subdirectory of an existing project
  --help -h             Display this message

This will create a basic directory structure at the path you specific, which looks like:
.
├── src/ 
├── script/
├── tests/
├── gaboon.toml
└── README.md
"""


def main() -> int:
    args: ParsedOptions = docopt(__doc__)
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
    counter_vyper_file = project_path.joinpath(COUNTER_CONTRACT_PATH)
    if not counter_vyper_file.exists():
        with counter_vyper_file.open("w") as fp:
            fp.write(COUNTER_VYPER_CONTRACT_SRC)
    for file in PROJECT_FILES:
        Path(project_path).joinpath(file).touch()
