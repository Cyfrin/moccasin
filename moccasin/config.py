from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TYPE_CHECKING, Union, cast
from moccasin.constants.vars import (
    CONFIG_NAME,
    DOT_ENV_FILE,
    CONTRACTS_FOLDER,
    BUILD_FOLDER,
    TESTS_FOLDER,
    SCRIPT_FOLDER,
    DEPENDENCIES_FOLDER,
    INSTALLER,
    DEFAULT_INSTALLER,
    SAVE_ABI_PATH,
)
import tomllib
from dotenv import load_dotenv
import os
import shutil
import tempfile
import boa
from boa.environment import Env
from moccasin.logging import logger
import tomlkit
from boa.contracts.vyper.vyper_contract import VyperDeployer, VyperContract
from boa.contracts.abi.abi_contract import ABIContractFactory, ABIContract
from moccasin.meta_contract import MetaContract

if TYPE_CHECKING:
    from boa.network import NetworkEnv
    from boa_zksync import ZksyncEnv


_AnyEnv = Union["NetworkEnv", "Env", "ZksyncEnv"]


@dataclass
class Network:
    name: str
    url: str | None = None
    is_fork: bool = False
    is_zksync: bool = False
    chain_id: int | None = None
    default_account_name: str | None = None
    unsafe_password_file: Path | None = None
    explorer_uri: str | None = None
    save_abi_path: str | None = None
    explorer_api_key: str | None = None
    contracts: dict[str, MetaContract] = field(default_factory=dict)
    extra_data: dict[str, Any] = field(default_factory=dict)
    _network_env: _AnyEnv | None = None

    def _create_env(self) -> _AnyEnv:
        # perf: save time on imports in the (common) case where
        # we just import config for its utils but don't actually need
        # to switch networks
        from boa.network import NetworkEnv, EthereumRPC
        from boa_zksync import ZksyncEnv

        if self.is_fork:
            self.set_fork(self.is_fork)
        else:
            if self.is_zksync:
                self._network_env = ZksyncEnv(EthereumRPC(self.url), nickname=self.name)
            else:
                self._network_env = NetworkEnv(
                    EthereumRPC(self.url), nickname=self.name
                )
        return self._network_env

    def set_fork(self, is_fork: bool):
        if self.is_fork != is_fork:
            self._network_env = Env()
            self._network_env = cast(_AnyEnv, self._network_env)
            boa.fork(self.url)  # This won't work for ZKSync?
            self._network_env.nickname = self.name

    def get_or_create_env(self, is_fork: bool) -> _AnyEnv:
        import boa

        self.set_fork(is_fork)
        if self._network_env:
            boa.set_env(self._network_env)
            return self._network_env
        new_env: _AnyEnv = self._create_env()
        boa.set_env(new_env)
        return new_env

    # TODO: Potentially rename to instantiate_contract
    def instantiate_contract(self, *args, **kwargs) -> VyperContract | ABIContract:
        return self.get_or_deploy_contract(*args, **kwargs)

    def manifest_contract(self, *args, **kwargs) -> VyperContract | ABIContract:
        return self.get_or_deploy_contract(*args, **kwargs)

    # TODO this function is way too big
    # TODO have this be a private function, and have a public function that is just like:
    # get_or_deploy_contract(contract_name, force_deploy, address)
    def get_or_deploy_contract(
        self,
        contract_name: str,
        force_deploy: bool = False,
        # TODO: Maybe remove this ABI shit
        abi: str
        | list
        | VyperDeployer
        | VyperContract
        | ABIContractFactory
        | ABIContract
        | None = None,
        abi_from_file_path: Path | str | None = None,
        abi_from_explorer: bool | None = None,
        deployer_path: str | Path | None = None,
        address: str | None = None,
    ) -> VyperContract | ABIContract:
        """Returns or deploys a VyperContract or ABIContract based on the name and address in the config file, or passed to this function.

        The following arguments are mutually exclusive:
            - abi
            - abi_from_file_path
            - abi_from_explorer

        Args:
            - contract_name: the contract name or deployer for the contract.
            - force_deploy: if True, will deploy the contract even if the contract has an address in the config file.
            - abi: the ABI of the contract. Can be a list, VyperDeployer, VyperContract, ABIContractFactory, or ABIContract.
            - abi_from_file_path: the path to the ABI file. Can be a .json or .vy file.
            - abi_from_explorer: if True, will fetch the ABI from the explorer.
            - deployer_path: If no address is given, this is the path to deploy the contract.
            - address: The address of the contract.

        Returns:
            VyperContract: The deployed contract instance, or a blank contract if the contract is not found.
        """
        meta_contract: MetaContract = self.contracts.get(
            contract_name, MetaContract(contract_name)
        )

        if (
            (abi and abi_from_file_path)
            or (abi and abi_from_explorer)
            or (abi_from_file_path and abi_from_explorer)
        ):
            raise ValueError(
                "Only one of abi, abi_from_file_path, or abi_from_explorer can be provided."
            )

        if not force_deploy:
            force_deploy = meta_contract.get("force_deploy", False)
        if not abi_from_file_path:
            abi_from_file_path = meta_contract.get("abi_from_file_path", None)
        if not abi_from_explorer:
            abi_from_explorer = meta_contract.get("abi_from_explorer", None)
        if not deployer_path:
            deployer_path = meta_contract.get("deployer_path", None)
        if not address:
            address = meta_contract.get("address", None)

        # 1. Check if force_deploy is true
        if force_deploy:
            if not deployer_path:
                raise ValueError(
                    f"Contract {meta_contract.contract_name} has force_deploy=True but no deployer_path specified in the config file."
                )
            return self._deploy_meta_contract(meta_contract, deployer_path)

        # 2. Setup ABI based on parameters
        abi: str | None = self._get_abi_from_params(
            meta_contract.contract_name,
            abi,
            abi_from_file_path,
            abi_from_explorer,
            address,
        )
        abi = abi if abi else meta_contract.abi

        # ------------------------------------------------------------------
        #             CHECK TO SEE IF WE'VE ALREADY DEPLOYED
        # ------------------------------------------------------------------
        # 3. Happy path, check if the requested contract is what we've already deployed
        if (
            meta_contract.abi == abi
            and meta_contract.address == address
            and meta_contract.vyper_contract
        ):
            return meta_contract.vyper_contract

        # 4. Happy path, maybe we didn't deploy the contract, but we've been given an abi and address, which works
        if abi and address:
            # Note, we are not putting this into the self.contracts dict, but maybe we should
            return ABIContractFactory(meta_contract.contract_name, abi).at(address)

        # ------------------------------------------------------------------
        #                      WE DEPLOY AFTER HERE
        # ------------------------------------------------------------------
        # 5. Check if there is an address, if no ABI, return a blank contract at an address
        if address and not abi:
            logger.info(
                f"No abi_source or abi_path found for {meta_contract.contract_name}, returning a blank contract at {address}"
            )
            # We could probably put this into _deploy_meta_contract with a conditional
            blank_contract: VyperDeployer = boa.loads_partial("")
            vyper_contract = blank_contract.at(address)
            meta_contract.update_from_deployment(vyper_contract)
            self.contracts[meta_contract.contract_name] = meta_contract

        # 6. If no address, deploy the contract
        if not address and not deployer_path:
            raise ValueError(
                f"Contract {meta_contract.contract_name} has no address or deployer_path specified in the config file."
            )
        return self._deploy_meta_contract(meta_contract, deployer_path)

    def _deploy_meta_contract(
        self, meta_contract: MetaContract, deployer_path: str | Path
    ) -> VyperContract:
        config = get_config()
        deployed_meta_contract: VyperContract = meta_contract._deploy(
            config.script_folder, deployer_path, update_from_deploy=True
        )
        self.contracts[meta_contract.contract_name] = meta_contract
        return deployed_meta_contract

    def _get_abi_from_params(
        self,
        logging_contract_name: str,
        abi: str
        | list
        | VyperDeployer
        | VyperContract
        | ABIContractFactory
        | ABIContract
        | None = None,
        abi_from_file_path: Path | str | None = None,
        abi_from_explorer: bool | None = None,
        address: str | None = None,
    ) -> str | None:
        abi = None
        # Validation
        if abi_from_explorer and not address:
            raise ValueError(
                f"Cannot get ABI from explorer without an address for contract {logging_contract_name}. Please provide an address."
            )

        # We want to get the ABI into ABI string format, aka this stuff: "[{}]"
        if abi:
            if isinstance(abi, list):
                abi = str(abi)
            if isinstance(abi, VyperDeployer):
                from vyper.compiler.output import build_abi_output

                abi = build_abi_output(abi.compiler_data)
            if (
                isinstance(abi, VyperContract)
                or isinstance(abi, ABIContractFactory)
                or isinstance(abi, ABIContract)
            ):
                abi = abi.abi
        if abi_from_file_path:  # Can be a json, VyperContract, or VyperInterface
            if isinstance(abi_from_file_path, str):
                config = get_config()
                if config.contracts_folder not in abi_from_file_path:
                    abi_from_file_path = (
                        f"{config.contracts_folder}/" + abi_from_file_path
                    )
            abi_path = Path(abi_from_file_path).resolve()
            # Check if the abi_path has .vy, .vyi, or .json extension
            if abi_path.suffix == ".json":
                abi = boa.load_abi(str(abi_path)).abi
            elif abi_path.suffix == ".vy":
                loaded_abi_from_deployer = boa.load_partial(str(abi_path))
                from vyper.compiler.output import build_abi_output

                abi = build_abi_output(loaded_abi_from_deployer.compiler_data)
            elif abi_path.suffix == ".vyi":
                raise NotImplementedError(
                    f"Loading an ABI from Vyper Interface files is not yet supported for contract {logging_contract_name}. You can track the progress here:\nhttps://github.com/vyperlang/vyper/issues/4232"
                )
            else:
                raise ValueError(
                    f"Invalid ABI file extension for {abi_path} for contract {logging_contract_name}. Must be .json, .vy, or .vyi"
                )
        if abi_from_explorer:
            from moccasin.commands.explorer import boa_get_abi_from_explorer

            abi = boa_get_abi_from_explorer(str(address), quiet=True)
        return abi

    @property
    def alias(self) -> str:
        return self.name

    @property
    def identifier(self) -> str:
        return self.name


class _Networks:
    _networks: dict[str, Network]
    _default_moccasin_contracts: dict[str, MetaContract]

    def __init__(self, toml_data: dict):
        self._networks = {}
        self._default_moccasin_contracts = {}
        self.custom_networks_counter = 0

        default_explorer_api_key = toml_data.get("project", {}).get(
            "explorer_api_key", None
        )
        default_explorer_uri = toml_data.get("project", {}).get("explorer_uri", None)
        default_save_abi_path = toml_data.get("project", {}).get("save_abi_path", None)
        default_contracts = toml_data.get("networks", {}).get("contracts", {})

        self._validate_network_contracts_dict(default_contracts)
        for contract_name, contract_data in default_contracts.items():
            self._default_moccasin_contracts[contract_name] = MetaContract(
                contract_name,
                force_deploy=contract_data.get("force_deploy", None),
                abi=contract_data.get("abi", None),
                abi_from_file_path=contract_data.get("abi_from_file_path", None),
                abi_from_etherscan=contract_data.get("abi_from_etherscan", None),
                deployer_path=contract_data.get("deployer_path", None),
                address=contract_data.get("address", None),
            )

        for network_name, network_data in toml_data["networks"].items():
            if network_name == "pyevm":
                raise ValueError(
                    "pyevm is a reserved network name, at this time, overriding defaults is not supported. Please remove it from your moccasin.toml."
                )
            if network_name == "contracts":
                continue
            else:
                starting_network_contracts_dict = network_data.get("contracts", {})
                self._validate_network_contracts_dict(
                    starting_network_contracts_dict, network_name=network_name
                )
                final_network_contracts = self._default_moccasin_contracts.copy()
                for (
                    contract_name,
                    contract_data,
                ) in starting_network_contracts_dict.items():
                    moccasin_contract = MetaContract(
                        contract_name,
                        force_deploy=contract_data.get("force_deploy", None),
                        abi=contract_data.get("abi", None),
                        abi_from_file_path=contract_data.get(
                            "abi_from_file_path", None
                        ),
                        abi_from_etherscan=contract_data.get(
                            "abi_from_etherscan", None
                        ),
                        deployer_path=contract_data.get("deployer_path", None),
                        address=contract_data.get("address", None),
                    )
                    if self._default_moccasin_contracts.get(contract_name, None):
                        moccasin_contract.set_defaults(
                            self._default_moccasin_contracts[contract_name]
                        )
                    final_network_contracts[contract_name] = moccasin_contract

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
                    contracts=final_network_contracts,
                    extra_data=network_data.get("extra_data", {}),
                )
                setattr(self, network_name, network)
                self._networks[network_name] = network

    def __len__(self):
        return len(self._networks)

    def get_active_network(self) -> Network:
        if boa.env.nickname in self._networks:
            return self._networks[boa.env.nickname]
        new_network = Network(
            name=boa.env.nickname, contracts=self._default_moccasin_contracts
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

    # TODO
    # REVIEW: i think it might be better to delegate to `boa.set_env`
    # so the usage would be like:
    # ```
    # boa.set_env_from_network(moccasin.networks.zksync)
    # ```
    # otherwise it is too confusing where moccasin ends and boa starts.
    def set_active_network(self, name_url_or_id: str | Network, is_fork: bool = False):
        env_to_set: _AnyEnv
        if isinstance(name_url_or_id, Network):
            env_to_set = name_url_or_id.get_or_create_env(is_fork)
            self._networks[name_url_or_id.name] = env_to_set
        else:
            if name_url_or_id.startswith("http"):
                new_network = self._create_custom_network(
                    name_url_or_id, is_fork=is_fork
                )
                env_to_set = new_network.get_or_create_env(is_fork)
            else:
                network = self.get_network(name_url_or_id)
                if network:
                    network.get_or_create_env(is_fork)
                else:
                    raise ValueError(
                        f"Network {name_url_or_id} not found. Please pass a valid URL/RPC or valid network name."
                    )

    def _create_custom_network(self, url: str, is_fork: bool = False) -> Network:
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
        load_dotenv(dotenv_path=self.project_root.joinpath(DOT_ENV_FILE))

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

    def set_active_network(self):
        self.networks.set_active_network(self)

    @property
    def installer(self) -> str:
        return self.project.get(INSTALLER, DEFAULT_INSTALLER)

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

    @staticmethod
    def load_config_from_path(config_path: Path | None = None) -> "Config":
        if config_path is None:
            config_path = Config.find_project_root()
        return Config(config_path)

    @staticmethod
    def find_project_root(start_path: Path | str = Path.cwd()) -> Path:
        current_path = Path(start_path).resolve()
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


def get_config() -> Config:
    global _config
    if _config is not None:
        return _config
    return initialize_global_config()


def initialize_global_config(config_path: Path | None = None) -> Config:
    global _config
    assert _config is None
    _config = Config.load_config_from_path(config_path)
    return _config
