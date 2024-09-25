import os
import shutil
import tempfile
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Union, cast

import boa
import tomlkit
from boa.contracts.abi.abi_contract import ABIContract, ABIContractFactory
from boa.contracts.vyper.vyper_contract import VyperContract, VyperDeployer
from boa.environment import Env
from boa_zksync import set_zksync_test_env
from dotenv import load_dotenv

from moccasin.constants.vars import (
    BUILD_FOLDER,
    CONFIG_NAME,
    CONTRACTS_FOLDER,
    DEPENDENCIES_FOLDER,
    DOT_ENV_FILE,
    DOT_ENV_KEY,
    SAVE_ABI_PATH,
    SCRIPT_FOLDER,
    TESTS_FOLDER,
    PYEVM,
    ERAVM,
    RESTRICTED_VALUES_FOR_LOCAL_NETWORK,
    DEFAULT_NETWORK,
)
from moccasin.logging import logger
from moccasin.named_contract import NamedContract

if TYPE_CHECKING:
    from boa.network import NetworkEnv
    from boa_zksync import ZksyncEnv

_AnyEnv = Union["NetworkEnv", "Env", "ZksyncEnv"]


@dataclass
class Network:
    name: str
    url: str | None = None
    chain_id: int | None = None
    is_fork: bool = False
    is_zksync: bool = False
    default_account_name: str | None = None
    unsafe_password_file: Path | None = None
    explorer_uri: str | None = None
    save_abi_path: str | None = None
    explorer_api_key: str | None = None
    contracts: dict[str, NamedContract] = field(default_factory=dict)
    prompt_live: bool = False
    extra_data: dict[str, Any] = field(default_factory=dict)
    _network_env: _AnyEnv | None = None

    def _create_boa_env(self) -> _AnyEnv:
        # perf: save time on imports in the (common) case where
        # we just import config for its utils but don't actually need
        # to switch networks
        from boa.network import EthereumRPC, NetworkEnv
        from boa_zksync import ZksyncEnv

        if self.name == PYEVM:
            self._network_env = Env()
        elif self.name == ERAVM:
            self._nework_env = set_zksync_test_env(nickname=ERAVM)
        elif self.is_zksync:
            self._network_env = ZksyncEnv(EthereumRPC(self.url), nickname=self.name)
        else:
            self._network_env = NetworkEnv(EthereumRPC(self.url), nickname=self.name)

        # Set fork
        if self.is_fork:
            self._network_env.fork(url=self.url, deprecated=False)

        return self._network_env

    def create_and_set_or_set_boa_env(self, **kwargs) -> _AnyEnv:
        for key, value in kwargs.items():
            setattr(self, key, value)

        if self._network_env is not None:
            boa.set_env(self._network_env)
            return self._network_env
        new_env: _AnyEnv = self._create_boa_env()
        boa.set_env(new_env)
        return new_env

    def manifest_contract(
        self, contract_name: str, force_deploy: bool = False, address: str | None = None
    ) -> VyperContract | ABIContract:
        """A wrapper around get_or_deploy_contract that is more explicit about the contract being deployed."""
        return self.get_or_deploy_contract(
            contract_name=contract_name, force_deploy=force_deploy, address=address
        )

    def instantiate_contract(self, *args, **kwargs) -> VyperContract | ABIContract:
        """An alias for get_or_deploy_contract."""
        return self.get_or_deploy_contract(*args, **kwargs)

    def get_or_deploy_contract(
        self,
        contract_name: str,
        force_deploy: bool = False,
        abi: str
        | Path
        | list
        | VyperDeployer
        | VyperContract
        | ABIContractFactory
        | ABIContract
        | None = None,
        abi_from_explorer: bool | None = None,
        deployer_script: str | Path | None = None,
        address: str | None = None,
    ) -> VyperContract | ABIContract:
        """Returns or deploys a VyperContract or ABIContract based on the name and address in the config file, or passed to this function.

        The following arguments are mutually exclusive:
            - abi
            - abi_from_explorer

        Args:
            - contract_name: the contract name or deployer for the contract.
            - force_deploy: if True, will deploy the contract even if the contract has an address in the config file.
            - abi: the ABI of the contract. Can be a list, string path to file, string of the ABI, VyperDeployer, VyperContract, ABIContractFactory, or ABIContract.
            - abi_from_explorer: if True, will fetch the ABI from the explorer.
            - deployer_script: If no address is given, this is the path to deploy the contract.
            - address: The address of the contract.

        Returns:
            VyperContract: The deployed contract instance, or a blank contract if the contract is not found.
        """
        named_contract: NamedContract = self.contracts.get(
            contract_name, NamedContract(contract_name)
        )

        if abi_from_explorer and abi:
            raise ValueError(
                "abi and abi_from_explorer are mutually exclusive. Please only provide one."
            )

        if not abi and not abi_from_explorer:
            abi = named_contract.get("abi", None)
            vyper_deployer = named_contract.get("vyper_deployer", None)
            if vyper_deployer:
                abi = vyper_deployer
        if not abi_from_explorer and not abi:
            abi_from_explorer = named_contract.get("abi_from_explorer", None)
        if not force_deploy:
            force_deploy = named_contract.get("force_deploy", False)
        if not deployer_script:
            deployer_script = named_contract.get("deployer_script", None)
        if not address:
            address = named_contract.get("address", None)

        # 1. Check if force_deploy is true
        if force_deploy:
            if not deployer_script:
                raise ValueError(
                    f"Contract {named_contract.contract_name} has force_deploy=True but no deployer_script specified in the config file."
                )
            return self._deploy_named_contract(named_contract, deployer_script)

        # 2. Setup ABI based on parameters
        abi = self._get_abi_or_deployer_from_params(
            named_contract.contract_name, abi, abi_from_explorer, address
        )
        abi = abi if abi else named_contract.abi

        # ------------------------------------------------------------------
        #             CHECK TO SEE IF WE'VE ALREADY DEPLOYED
        # ------------------------------------------------------------------
        # 3. Happy path, check if the requested contract is what we've already deployed
        if (
            named_contract.abi == abi
            and named_contract.address == address
            and named_contract.vyper_contract
        ):
            return named_contract.vyper_contract

        # 4. Happy path, maybe we didn't deploy the contract, but we've been given an abi and address, which works
        if abi and address:
            if isinstance(abi, VyperDeployer):
                return abi.at(address)
            else:
                # Note, we are not putting this into the self.contracts dict, but maybe we should
                return ABIContractFactory(named_contract.contract_name, abi).at(address)

        # ------------------------------------------------------------------
        #                      WE DEPLOY AFTER HERE
        # ------------------------------------------------------------------
        # 5. Check if there is an address, if no ABI, return a blank contract at an address
        if address and not abi:
            logger.info(
                f"No abi_source or abi_path found for {named_contract.contract_name}, returning a blank contract at {address}"
            )
            # We could probably put this into _deploy_named_contract with a conditional
            blank_contract: VyperDeployer = boa.loads_partial("")
            vyper_contract = blank_contract.at(address)
            named_contract.update_from_deployment(vyper_contract)
            self.contracts[named_contract.contract_name] = named_contract
            return vyper_contract

        # 6. If no address, deploy the contract
        if not deployer_script:
            raise ValueError(
                f"Contract {named_contract.contract_name} has no address or deployer_script specified in the config file."
            )

        return self._deploy_named_contract(named_contract, deployer_script)

    def is_testing_network(self) -> bool:
        """Returns True if network is:
        1. pyevm
        2. eravm
        3. A fork
        """
        return self.name in [PYEVM, ERAVM] or self.is_fork

    def _deploy_named_contract(
        self, named_contract: NamedContract, deployer_script: str | Path
    ) -> VyperContract:
        config = get_config()
        deployed_named_contract: VyperContract = named_contract._deploy(
            config.script_folder, deployer_script, update_from_deploy=True
        )
        self.contracts[named_contract.contract_name] = named_contract
        return deployed_named_contract

    def _get_abi_or_deployer_from_params(
        self,
        logging_contract_name: str,
        abi: str
        | Path
        | list
        | VyperDeployer
        | VyperContract
        | ABIContractFactory
        | ABIContract
        | None = None,
        abi_from_explorer: bool | None = None,
        address: str | None = None,
    ) -> str | VyperDeployer | None:
        if abi_from_explorer and not address:
            raise ValueError(
                f"Cannot get ABI from explorer without an address for contract {logging_contract_name}. Please provide an address."
            )

        config = get_config()
        # TODO, test these branches
        if abi:
            if isinstance(abi, str):
                # Check if it's a file path
                if abi.endswith(".json") or abi.endswith(".vy") or abi.endswith(".vyi"):
                    abi_path = config._find_contract(abi)
                    if abi.endswith(".vy"):
                        abi = boa.load_partial(str(abi_path))
                    elif abi_path.suffix == ".json":
                        abi = boa.load_abi(str(abi_path)).abi
                    elif abi_path.suffix == ".vyi":
                        raise NotImplementedError(
                            f"Loading an ABI from Vyper Interface files is not yet supported for contract {logging_contract_name}. You can track the progress here:\nhttps://github.com/vyperlang/vyper/issues/4232"
                        )
                # Else, it's just a contract name
                else:
                    contract_path = config._find_contract(abi)
                    abi = boa.load_partial(str(contract_path))
            if isinstance(abi, list):
                # If its an ABI, just take it
                return str(abi)
            if isinstance(abi, VyperDeployer):
                return abi
            if isinstance(abi, VyperContract):
                return abi.deployer
            if isinstance(abi, ABIContractFactory):
                return abi.abi
            if isinstance(abi, ABIContract):
                return abi.abi

        if abi_from_explorer:
            from moccasin.commands.explorer import boa_get_abi_from_explorer

            abi = boa_get_abi_from_explorer(str(address), quiet=True)
        return abi  # type: ignore

    def get_named_contract(self, contract_name: str) -> NamedContract | None:
        return self.contracts.get(contract_name, None)

    @property
    def alias(self) -> str:
        return self.name

    @property
    def identifier(self) -> str:
        return self.name


class _Networks:
    _networks: dict[str, Network]
    _default_named_contracts: dict[str, NamedContract]
    default_network_name: str

    def __init__(self, toml_data: dict):
        self._networks = {}
        self._default_named_contracts = {}
        self.custom_networks_counter = 0
        project_data = toml_data.get("project", {})

        default_explorer_api_key = project_data.get("explorer_api_key", None)
        default_explorer_uri = project_data.get("explorer_uri", None)
        default_save_abi_path = project_data.get("save_abi_path", None)
        default_contracts = toml_data.get("networks", {}).get("contracts", {})
        self.default_network_name = project_data.get(
            "default_network_name", DEFAULT_NETWORK
        )

        self._validate_network_contracts_dict(default_contracts)
        for contract_name, contract_data in default_contracts.items():
            self._default_named_contracts[contract_name] = NamedContract(
                contract_name,
                force_deploy=contract_data.get("force_deploy", None),
                abi=contract_data.get("abi", None),
                abi_from_explorer=contract_data.get("abi_from_explorer", None),
                deployer_script=contract_data.get("deployer_script", None),
                address=contract_data.get("address", None),
            )

        for network_name, network_data in toml_data["networks"].items():
            # Check for restricted items for pyevm or eravm
            if network_name in [PYEVM, ERAVM]:
                for key in network_data.keys():
                    if key in RESTRICTED_VALUES_FOR_LOCAL_NETWORK:
                        raise ValueError(
                            f"Cannot set {key} for network {network_name}."
                        )

            if network_name == "contracts":
                continue
            else:
                starting_network_contracts_dict = network_data.get("contracts", {})
                self._validate_network_contracts_dict(
                    starting_network_contracts_dict, network_name=network_name
                )
                final_network_contracts = (
                    self._generate_network_contracts_from_defaults(
                        self._default_named_contracts.copy(),
                        starting_network_contracts_dict,
                    )
                )
                network = Network(
                    name=network_name,
                    is_fork=network_data.get("fork", False),
                    url=network_data.get("url", None),
                    is_zksync=network_data.get("zksync", False),
                    chain_id=network_data.get("chain_id", None),
                    explorer_uri=network_data.get("explorer_uri", default_explorer_uri),
                    save_abi_path=network_data.get(
                        SAVE_ABI_PATH, default_save_abi_path
                    ),
                    explorer_api_key=network_data.get(
                        "explorer_api_key", default_explorer_api_key
                    ),
                    default_account_name=network_data.get("default_account_name", None),
                    unsafe_password_file=network_data.get("unsafe_password_file", None),
                    prompt_live=network_data.get("prompt_live", False),
                    contracts=final_network_contracts,
                    extra_data=network_data.get("extra_data", {}),
                )
                setattr(self, network_name, network)
                self._networks[network_name] = network

    def __len__(self):
        return len(self._networks)

    def _generate_network_contracts_from_defaults(
        self, starting_default_contracts: dict, starting_network_contracts_dict: dict
    ) -> dict:
        for contract_name, contract_data in starting_network_contracts_dict.items():
            named_contract = NamedContract(
                contract_name,
                force_deploy=contract_data.get("force_deploy", None),
                abi=contract_data.get("abi", None),
                abi_from_explorer=contract_data.get("abi_from_explorer", None),
                deployer_script=contract_data.get("deployer_script", None),
                address=contract_data.get("address", None),
            )
            if self._default_named_contracts.get(contract_name, None):
                named_contract.set_defaults(
                    self._default_named_contracts[contract_name]
                )
            starting_default_contracts[contract_name] = named_contract
        return starting_default_contracts

    def get_active_network(self) -> Network:
        if boa.env.nickname in self._networks:
            return self._networks[boa.env.nickname]
        new_network = Network(
            name=boa.env.nickname, contracts=self._default_named_contracts
        )
        self._networks[new_network.name] = new_network
        return new_network

    def get_network(self, network_name_or_id: str | int) -> Network:
        if isinstance(network_name_or_id, int):
            return self.get_network_by_chain_id(network_name_or_id)
        else:
            if network_name_or_id.isdigit():
                return self.get_network_by_chain_id(int(network_name_or_id))
        return self.get_network_by_name(network_name_or_id)

    def get_network_by_chain_id(self, chain_id: int) -> Network:
        for network in self._networks.values():
            if network.chain_id == chain_id:
                return network
        raise ValueError(f"Network with chain_id {chain_id} not found.")

    def get_network_by_name(self, alias: str) -> Network:
        network = self._networks.get(alias, None)
        if not network:
            raise ValueError(f"Network {alias} not found.")
        return network

    def get_or_deploy_contract(self, *args, **kwargs) -> VyperContract | ABIContract:
        return self.get_active_network().get_or_deploy_contract(*args, **kwargs)

    def set_active_network(self, name_of_network_or_network: str | Network, **kwargs):
        env_to_set: _AnyEnv
        if isinstance(name_of_network_or_network, str):
            name_of_network_or_network = self.get_network(name_of_network_or_network)
            name_of_network_or_network = cast(Network, name_of_network_or_network)

        env_to_set = name_of_network_or_network.create_and_set_or_set_boa_env(**kwargs)
        self._networks[name_of_network_or_network.name] = env_to_set

    def _create_custom_network(self, url: str, is_fork: bool | None = False) -> Network:
        if is_fork is None:
            is_fork = False
        new_network = Network(
            name=f"custom_{self.custom_networks_counter}", url=url, is_fork=is_fork
        )
        self._networks[new_network.name] = new_network
        self.custom_networks_counter += 1
        return new_network

    @staticmethod
    def _validate_network_contracts_dict(
        contracts: Any, network_name: str | None = None
    ):
        network_name = f"{network_name}." if network_name else ""

        if not isinstance(contracts, dict):
            logger.error(f"networks.{network_name}contracts")
            raise ValueError(f"Contracts must be a dictionary in your {CONFIG_NAME}.")

        for contract in contracts:
            if not isinstance(contracts[contract], dict):
                logger.error(f"networks.contracts.{contract}")
                raise ValueError(
                    f"Contracts must be a dictionary in your {CONFIG_NAME}."
                )


class Config:
    _project_root: Path
    networks: _Networks
    dependencies: list[str]
    project: dict[str, str]
    extra_data: dict[str, Any]

    def __init__(self, root_path: Path):
        self._project_root = root_path
        config_path: Path = root_path.joinpath(CONFIG_NAME)
        if config_path.exists():
            self._load_config(config_path)

    def _load_config(self, config_path: Path):
        toml_data: dict = self.read_moccasin_config(config_path)
        # Need to get the .env file before expanding env vars
        self.project = {}
        self.project[DOT_ENV_KEY] = toml_data.get("project", {}).get(
            DOT_ENV_KEY, DOT_ENV_FILE
        )
        self._load_env_file()
        toml_data = self.expand_env_vars(toml_data)
        self.networks = _Networks(toml_data)
        self.dependencies = toml_data.get("project", {}).get("dependencies", [])
        self.project = toml_data.get("project", {})
        if TESTS_FOLDER in self.project:
            logger.warning(
                f"Tests folder is set to {self.project[TESTS_FOLDER]}. This is not supported and will be ignored."
            )
        self.extra_data = toml_data.get("extra_data", {})

    def _load_env_file(self):
        load_dotenv(dotenv_path=self.project_root.joinpath(self.dot_env))

    def read_moccasin_config(self, config_path: Path = None) -> dict:
        config_path = self._validate_config_path(config_path)
        with open(config_path, "rb") as f:
            return tomllib.load(f)

    def read_moccasin_config_preserve_comments(
        self, config_path: Path = None
    ) -> tomlkit.TOMLDocument:
        config_path = self._validate_config_path(config_path)
        with open(config_path, "rb") as f:
            return tomlkit.load(f)

    def _validate_config_path(self, config_path: Path = None) -> Path:
        if not config_path:
            config_path = self._project_root
        if not str(config_path).endswith(f"/{CONFIG_NAME}"):
            config_path = config_path.joinpath(CONFIG_NAME)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        return config_path

    def expand_env_vars(self, value):
        if isinstance(value, str):
            return os.path.expandvars(value)
        elif isinstance(value, dict):
            return {k: self.expand_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.expand_env_vars(item) for item in value]
        return value

    def get_active_network(self):
        return self.networks.get_active_network()

    def get_or_deploy_contract(self, *args, **kwargs) -> VyperContract | ABIContract:
        return self.get_active_network().get_or_deploy_contract(*args, **kwargs)

    def get_dependencies(self) -> list[str]:
        return self.dependencies

    def write_dependencies(self, dependencies: list):
        target_path = self._project_root / CONFIG_NAME
        toml_data = self.read_moccasin_config_preserve_comments(target_path)
        toml_data["project"]["dependencies"] = dependencies  # type: ignore

        # Create a temporary file in the same directory as the target file
        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            dir=target_path.parent,
            prefix=".tmp_",
            suffix=".toml",
        )
        try:
            temp_file.write(tomlkit.dumps(toml_data))
            temp_file.close()
            shutil.move(temp_file.name, target_path)
        except Exception as e:
            os.unlink(temp_file.name)
            raise e

        self.dependencies = dependencies

    def get_base_dependencies_install_path(self) -> Path:
        project_root = self._project_root
        base_install_path = project_root / self.project.get(
            DEPENDENCIES_FOLDER, DEPENDENCIES_FOLDER
        )
        base_install_path.mkdir(exist_ok=True, parents=True)
        return base_install_path

    def get_root(self) -> Path:
        return self._project_root

    def _find_contract(self, contract_or_contract_path: str) -> Path:
        config_root = self.get_root()

        # If the path starts with '~', expand to the user's home directory
        contract_path = Path(contract_or_contract_path).expanduser()

        # If the path is already absolute and exists, return it directly
        if contract_path.is_absolute() and contract_path.exists():
            return contract_path

        # Handle contract names without ".vy" by appending ".vy"
        if not contract_path.suffix == ".vy":
            contract_path = contract_path.with_suffix(".vy")

        # If the contract path is relative, check if it exists relative to config_root
        if not contract_path.is_absolute():
            contract_path = config_root / contract_path
            if contract_path.exists():
                return contract_path

        # Search for the contract in the contracts folder if not found by now
        contracts_location = config_root / self.contracts_folder
        contract_paths = list(contracts_location.rglob(contract_path.name))

        if not contract_paths:
            raise FileNotFoundError(
                f"Contract file '{contract_path.name}' not found under '{contracts_location}'."
            )
        elif len(contract_paths) > 1:
            found_paths = "\n".join(str(path) for path in contract_paths)
            raise FileExistsError(
                f"Multiple contract files named '{contract_path.name}' found:\n{found_paths}\n"
                "Please specify the full path to the contract file."
            )

        # Return the single found contract
        return contract_paths[0]

    def set_active_network(self, name_url_or_id: str | Network, **kwargs):
        self.networks.set_active_network(name_url_or_id, **kwargs)

    @property
    def project_root(self) -> Path:
        return self._project_root

    @property
    def build_folder(self) -> str:
        return self.project.get(BUILD_FOLDER, BUILD_FOLDER)

    @property
    def out_folder(self) -> str:
        return self.build_folder

    @property
    def contracts_folder(self) -> str:
        return self.project.get(CONTRACTS_FOLDER, CONTRACTS_FOLDER)

    @property
    def src_folder(self) -> str:
        return self.contracts_folder

    @property
    def cov_config(self) -> str | None:
        return self.project.get("cov_config", None)

    @property
    def dot_env(self) -> str:
        return self.project.get(DOT_ENV_KEY, DOT_ENV_FILE)

    # Tests must be in "tests" folder
    @property
    def test_folder(self) -> str:
        return TESTS_FOLDER

    @property
    def script_folder(self) -> str:
        return self.project.get(SCRIPT_FOLDER, SCRIPT_FOLDER)

    @property
    def lib_folder(self) -> str:
        return self.project.get(DEPENDENCIES_FOLDER, DEPENDENCIES_FOLDER)

    @property
    def default_network(self) -> str:
        return self.project.get("default_network", DEFAULT_NETWORK)

    @staticmethod
    def load_config_from_path(config_path: Path | None = None) -> "Config":
        if config_path is None:
            config_path = Config.find_project_root()
        return Config(config_path)

    @staticmethod
    def find_project_root(start_path: Path | str = Path.cwd()) -> Path:
        current_path = Path(start_path).expanduser().resolve()
        while True:
            # Move up to the parent directory
            parent_path = current_path.parent
            if parent_path == current_path:
                # We've reached the root directory without finding moccasin.toml
                raise FileNotFoundError(
                    "Could not find moccasin.toml or src directory with Vyper contracts in any parent directory"
                )

            if (current_path / CONFIG_NAME).exists():
                return current_path

            # Check for src directory with .vy files in current directory
            src_path = current_path / "src"
            if src_path.is_dir() and any(src_path.glob("*.vy")):
                return current_path

            current_path = parent_path


_config: Config | None = None


def get_or_initialize_config() -> Config:
    global _config
    if _config is None:
        _config = initialize_global_config()
    return _config


def get_config() -> Config:
    """Get the global Config object."""
    global _config
    if _config is None:
        raise ValueError(
            "Global Config object not initialized, initialize with initialize_global_config"
        )
    return _config


def initialize_global_config(config_path: Path | None = None) -> Config:
    global _config
    assert _config is None
    _config = Config.load_config_from_path(config_path)
    return _config
