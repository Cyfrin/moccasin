from pathlib import Path
from typing import Any, Optional

from .gaboon_config import GaboonConfig


class Project:
    # Attributes
    # ========================================================================
    root: Path
    config: GaboonConfig
    project_path: Path

    # Constructors
    # ========================================================================
    def __init__(self, path: Optional[Path] = None):
        self.root: Path = self.find_project_root(path or Path.cwd())
        self.config: GaboonConfig = self._load_config()

    # Special Methods
    # ========================================================================
    def __getattr__(self, name: str) -> Any:
        if name in self.config.active_profile:
            return self.config.active_profile[name]
        try:
            return getattr(self.config, name)
        except AttributeError:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

    # Internal Methods
    # ========================================================================
    def _load_config(self) -> GaboonConfig:
        return GaboonConfig(self.root)

    # Static Methods
    # ========================================================================
    @staticmethod
    def find_project_root(start_path: Path | str = Path.cwd()) -> Path:
        current_path = Path(start_path).resolve()
        while True:
            if (current_path / "gaboon.toml").exists():
                return current_path

            # Check for src directory with .vy files in current directory
            src_path = current_path / "src"
            if src_path.is_dir() and any(src_path.glob("*.vy")):
                return current_path

            # Check for gaboon.toml in parent directory
            if (current_path.parent / "gaboon.toml").exists():
                return current_path.parent

            # Move up to the parent directory
            parent_path = current_path.parent
            if parent_path == current_path:
                # We've reached the root directory without finding gaboon.toml
                raise FileNotFoundError(
                    "Could not find gaboon.toml or src directory with Vyper contracts in any parent directory"
                )
            current_path = parent_path
