import os
import tomllib
from pathlib import Path
from typing import Union

DEFAULT_VYPER_VERSION = "0.4.0"

GABOON_DEFAULT_CONFIG = {
    "profile": {
        "default": {
            "src": "src",
            "test": "tests",
            "script": "script",
            "out": "out",
            "libs": ["lib"],
            "remappings": [],
        }
    }
}

GABOON_PROFILE_ENV_VAR = "GABOON_PROFILE"
FOUNDRY_PROFILE_ENV_VAR = "FOUNDRY_PROFILE"
DEFAULT_PROFILE_NAME = "default"


class GaboonConfig:
    # Attributes
    # ========================================================================
    profile: str | None
    config_data: dict
    active_profile: dict

    # Constructors
    # ========================================================================
    def __init__(
        self, config_source: Union[dict, Path] | None, profile: str | None = None
    ):
        if isinstance(config_source, dict):
            self.set_config_data(config_source, profile)
        elif isinstance(config_source, Path):
            self._init_from_path(config_source)
        elif config_source is None:
            self.set_config_data(GABOON_DEFAULT_CONFIG)

    def _init_from_path(self, config_path: Path):
        config_data = self.read_gaboon_config(config_path)
        self.set_config_data(config_data)

    # Special Methods
    # ========================================================================
    def __repr__(self):
        return f"GaboonConfig({self.active_profile})"

    def __str__(self):
        return self.__repr__()

    # Public Methods
    # ========================================================================
    def set_config_data(self, config_data: dict, profile: str | None = None):
        if profile is None:
            profile = os.getenv(GABOON_PROFILE_ENV_VAR) or os.getenv(
                FOUNDRY_PROFILE_ENV_VAR
            )
            if profile:
                self.profile = profile
            else:
                self.profile = DEFAULT_PROFILE_NAME
        self.config_data = config_data
        self.active_profile = self.config_data["profile"][self.profile]

    def read_gaboon_config(self, config_path: Path) -> dict:
        if not str(config_path).endswith("/gaboon.toml"):
            config_path = config_path.joinpath("gaboon.toml")
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with open(config_path, "rb") as f:
            return tomllib.load(f)
