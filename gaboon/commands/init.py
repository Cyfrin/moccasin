from pathlib import Path
from gaboon.logging import logger
import tomli_w
from typing import Any, List
from gaboon.constants import (
    CONFIG_NAME,
    PROJECT_FOLDERS,
    GITIGNORE,
    GITATTRIBUTES,
    README_PATH,
    README_MD_SRC,
    COUNTER_CONTRACT_PATH,
    COUNTER_VYPER_CONTRACT_SRC,
    GAB_DEFAULT_CONFIG,
    CONFTEST_DEFAULT,
    DEPLOY_SCRIPT_DEFAULT,
    TEST_COUNTER_DEFAULT
)


def main(args: List[Any]) -> int:
    path: str = new_project(args.path or ".", args.force or False)
    logger.info(f"Project initialized at {path}")
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
        raise FileExistsError(
            f"Directory is not empty: {project_path}.\nIf you're sure the folder is ok to potentially overwrite, try creating a new project by running with `gab init --force`"
        )
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
    toml_file = project_path.joinpath(CONFIG_NAME)
    with open(toml_file, "wb") as f:
        tomli_w.dump(GAB_DEFAULT_CONFIG, f)
    readme_file = project_path.joinpath(README_PATH)
    with open(readme_file, "w") as f:
        f.write(README_MD_SRC)
    conftest_file = project_path.joinpath("tests/conftest.py")
    with open(conftest_file, "w") as f:
        f.write(CONFTEST_DEFAULT)
    deploy_file = project_path.joinpath("script/deploy.py")
    with open(deploy_file, "w") as f:
        f.write(DEPLOY_SCRIPT_DEFAULT)
    test_counter_file = project_path.joinpath("tests/test_counter.py")
    with open(test_counter_file, "w") as f:
        f.write(TEST_COUNTER_DEFAULT)