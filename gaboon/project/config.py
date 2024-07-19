import tomllib
from pathlib import Path
from typing import Optional

DEFAULT_VYPER_VERSION = "0.4.0"
BASE_TOML_CONFIG_PATH = Path(__file__).parent.joinpath("base_config.toml")
BASE_CONFIG_VALUES = ["src", "test", "script", "out", "libs", "remappings"]


class GaboonConfig:
    def __init__(self, config_path: Optional[Path] = None):
        with open(BASE_TOML_CONFIG_PATH, "rb") as f:
            config_data = tomllib.load(f)
            self._load_config_data(config_data)

        if config_path is not None:
            with open(config_path, "rb") as f:
                config_data = tomllib.load(f)
                self._load_config_data(config_data)

    def __str__(self) -> str:
        attributes = {key: getattr(self, key, "Not Set") for key in BASE_CONFIG_VALUES}
        formatted_attributes = ", ".join(
            f"{key}={value}" for key, value in attributes.items()
        )
        return f"{self.__class__.__name__}({formatted_attributes})"

    def _load_config_data(self, config_data):
        for _, settings in config_data.get("profile", {}).items():
            for key, value in settings.items():
                setattr(self, key, value)
                setattr(self, key, value)
