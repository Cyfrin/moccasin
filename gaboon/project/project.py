from pathlib import Path
from typing import Optional, Union

from .config import GaboonConfig


class Project:
    def __init__(
        self,
        project_path: Path,
    ):
        self._path: Path = project_path
        self.config: GaboonConfig = GaboonConfig(
            config_path=project_path.joinpath("gaboon.toml")
        )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self._path})"


def find_project_home(
    path: Union[Path, str] = ".",
) -> Optional[Path]:
    """
    Recursively search for a gaboon.toml file in the parent directories.

    :param start_path: The directory to start the search from.
    :return: The path to the gaboon.toml file if found, otherwise None.
    """
    path = Path(path)
    current_path = Path(path).resolve()
    while current_path != current_path.parent:
        gaboon_toml_path = current_path.joinpath("gaboon.toml")
        if gaboon_toml_path.exists():
            return current_path
        current_path = current_path.parent
    return None
