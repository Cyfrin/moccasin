from dataclasses import dataclass, astuple
from pathlib import Path
from typing import Any, Union
from boa.network import NetworkEnv, EthereumRPC
import boa
from gaboon.constants import CONFIG_NAME
import tomllib


@dataclass
class Network:
    name: str
    url: str | None
    extra_data: dict[str, Any] | None
    _network_env: NetworkEnv | None = None

    def _create_env(self) -> NetworkEnv:
        self._network_env = NetworkEnv(EthereumRPC(self.url, nickmane=self.name))
        return self._network_env

    def __eq__(self, other: Union[str, "Network"]) -> bool:
        if isinstance(other, str):
            return self.name == other
        if isinstance(other, self.__class__):
            return astuple(self) == astuple(other)
        return False

    @property
    def alias(self) -> str:
        return self.name
    
    @property 
    def identifier(self) -> str: 
        return self.name
    
    

class _Networks:
    _networks: dict[str, Network]

    def __init__(self, toml_data: dict):
        self._networks = {}
        for key, value in toml_data["networks"].items():
            network = Network(name=key, url=value.get("url", None), extra_data=value.get("extra_data", {}))
            setattr(self, key, network)
            self._networks[key] = network
    
    def __getattr__(self, name: str) -> Network:
        if name in self._networks:
            return self._networks[name]
        raise AttributeError(f"Network '{name}' not found")

    def __iter__(self):
        return iter(self._networks.values())

    def __len__(self):
        return len(self._networks)

    def get_active_network(self) -> Network:
        if boa.env.nickname in self._networks:
            return self._networks[boa.env.nickname]
        else:
            new_network = Network(name=boa.env.nickname)
            self._networks[new_network.name] = new_network
            return new_network

    def get_network_by_name(self, alias: str) -> Network:
        return self._networks[alias]
    
    def set_active_network(self, name: str):
        if self._networks[name]._network_env:
            boa.set_env(self._networks[name]._network_env)
        else:
            boa.set_env(self._networks[name]._create_env())


class Config:
    _root_path: Path
    networks: _Networks
    extra_data: dict[str, str] | None

    def __init__(self, root_path: Path):
        self._root_path = root_path
        config_path: Path = root_path.joinpath(CONFIG_NAME)
        if config_path.exists():
            self._load_config(config_path)
    
    def _load_config(self, config_path: Path):
        toml_data: dict = self.read_gaboon_config(config_path)
        self.networks = _Networks(toml_data)
    
    def read_gaboon_config(self, config_path: Path) -> dict:
        if not str(config_path).endswith("/gaboon.toml"):
            config_path = config_path.joinpath("gaboon.toml")
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with open(config_path, "rb") as f:
            return tomllib.load(f)
        

    def get_active_network(self):
        return self.networks.get_active_network()
    
    def get_root(self) -> Path:
        return self._root_path
    
    @staticmethod 
    def load_config_from_path(config_path: Path | None = None) -> "Config":
        if config_path is None:
            config_path = Config.find_project_root()
        return Config(config_path)
        

    @staticmethod
    def find_project_root(start_path: Path | str = Path.cwd()) -> Path:
        current_path = Path(start_path).resolve()
        while True:
            if (current_path / CONFIG_NAME).exists():
                return current_path

            # Check for src directory with .vy files in current directory
            src_path = current_path / "src"
            if src_path.is_dir() and any(src_path.glob("*.vy")):
                return current_path

            # Check for gaboon.toml in parent directory
            if (current_path.parent / CONFIG_NAME).exists():
                return current_path.parent

            # Move up to the parent directory
            parent_path = current_path.parent
            if parent_path == current_path:
                # We've reached the root directory without finding gaboon.toml
                raise FileNotFoundError(
                    "Could not find gaboon.toml or src directory with Vyper contracts in any parent directory"
                )
            current_path = parent_path



_config: Config = None

def get_config() -> Config:
    global _config
    return _config


def initialize_global_config():
    global _config
    assert _config is None
    _config = Config.load_config_from_path()
