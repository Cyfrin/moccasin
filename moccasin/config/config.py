"""
@dev It can still be refined. Maybe with more expertise?
    Architecture review?
"""

import os
import shutil
import tempfile
import tomllib
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Tuple, Union, cast

import boa
import tomlkit
from boa.contracts.abi.abi_contract import ABIContract, ABIContractFactory
from boa.contracts.vyper.vyper_contract import (
    VyperContract,
    VyperDeployer,
    build_abi_output,
)
from boa.deployments import Deployment, DeploymentsDB, get_deployments_db
from boa.verifiers import get_verification_bundle
from boa_zksync.contract import ZksyncContract
from boa_zksync.deployer import ZksyncDeployer
from dotenv import load_dotenv
from tomlkit.items import Table

from moccasin.constants.vars import (
    BUILD_FOLDER,
    CONFIG_NAME,
    CONTRACTS_FOLDER,
    DB_PATH_LIVE_DEFAULT,
    DEFAULT_NETWORK,
    DEPENDENCIES_FOLDER,
    DOT_ENV_FILE,
    DOT_ENV_KEY,
    ERAVM,
    FORK_NETWORK_DEFAULTS,
    LOCAL_NETWORK_DEFAULTS,
    PYEVM,
    RESTRICTED_VALUES_FOR_LOCAL_NETWORK,
    SAVE_ABI_PATH,
    SAVE_TO_DB,
    SCRIPT_FOLDER,
    SPECIFIC_VALUES_FOR_ALL_LOCAL_NETWORKS,
    TESTS_FOLDER,
)
from moccasin.logging import logger
from moccasin.named_contract import NamedContract

from .base_network import BaseNetwork

if TYPE_CHECKING:
    from boa.verifiers import Blockscout
    from boa_zksync.verifiers import ZksyncExplorer

VERIFIERS = Union["Blockscout", "ZksyncExplorer"]


################################################################
#                     NETWORK BASED CONFIG                     #
################################################################
class Network(BaseNetwork):
    """
    Subclass of BaseNetwork to implement methods related to configuration.

    @dev To avoid circular imports
    """

    def _get_deployments_iterator(
        self,
        contract_name: str | None = None,
        chain_id: int | str | None = None,
        limit: int | None = None,
        config_or_db_path: Union["Config", Path, str, None] = None,
    ) -> Iterator[Deployment]:
        """Get deployments from the database without an initialized config."""
        db_path = None
        if isinstance(config_or_db_path, Config):
            db_path = config_or_db_path._toml_data.get("db_path", ".deployments.db")
        elif isinstance(db_path, str):
            db_path = Path(db_path)
        elif isinstance(config_or_db_path, Path):
            db_path = config_or_db_path
        if not db_path:
            db = get_deployments_db()
        else:
            db = DeploymentsDB(db_path)
        if db is None:
            logger.warning(
                "No deployments database found. Returning an empty iterator."
            )
            return iter([])
        else:
            return self._fetch_deployments_from_db(
                contract_name=contract_name, chain_id=chain_id, limit=limit, db=db
            )

    def get_deployments_unchecked(
        self,
        contract_name: str | None = None,
        limit: int | None = None,
        chain_id: int | str | None = None,
        config_or_db_path: Union["Config", Path, str, None] = None,
    ) -> list[Deployment]:
        deployments_iter = self._get_deployments_iterator(
            contract_name=contract_name,
            chain_id=chain_id,
            limit=limit,
            config_or_db_path=config_or_db_path,
        )
        return list(deployments_iter)

    def get_deployments_checked(
        self,
        contract_name: str | None = None,
        limit: int | None = None,
        chain_id: int | str | None = None,
        config_or_db_path: Union["Config", Path, str, None] = None,
    ) -> list[Deployment]:
        deployments_iter = self._get_deployments_iterator(
            contract_name=contract_name,
            chain_id=chain_id,
            limit=limit,
            config_or_db_path=config_or_db_path,
        )

        config = config_or_db_path
        if not isinstance(config_or_db_path, Config):
            config = get_config()
        config = cast(Config, config)

        deployments_list = []
        for deployment in deployments_iter:
            if self.has_matching_integrity(deployment, contract_name, config=config):
                deployments_list.append(deployment)
        return deployments_list

    def has_matching_integrity(
        self,
        deployment: Deployment,
        contract_name: str | None,
        config: Union["Config", None] = None,
    ) -> bool:
        if config is None:
            config = get_config()
        if contract_name is None:
            raise ValueError("contract_name cannot be None.")
        vyper_deployer = self.get_deployer_from_contract_name(config, contract_name)
        # REVIEW: If boa throws a warning, maybe that's all we need instead of checking the integrity
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message="casted bytecode does not match compiled bytecode at*"
            )
            contract = vyper_deployer.at(deployment.contract_address)
        verification_bundle = get_verification_bundle(contract)
        expected_integrity = verification_bundle["integrity"]
        actual_integrity = deployment.source_code["integrity"]
        if expected_integrity != actual_integrity:
            return False
        return True

    def get_deployer_from_contract_name(
        self, config: "Config", contract_name: str
    ) -> VyperDeployer | ZksyncDeployer:
        contract_path = config.find_contract(contract_name)
        return boa.load_partial(str(contract_path.absolute()))

    def _deploy_named_contract(
        self, named_contract: NamedContract, deployer_script: str | Path
    ) -> VyperContract | ZksyncContract:
        config = get_config()
        deployed_named_contract: VyperContract | ZksyncContract = (
            named_contract._deploy(config.script_folder, deployer_script)
        )
        self.named_contracts[named_contract.contract_name] = named_contract
        if self.save_to_db:
            if not self.is_local_or_forked_network():
                added = self._add_named_to_db(named_contract)
                if not added:
                    logger.error(
                        f"Could not add contract_name to database for contract {named_contract.contract_name}."
                    )
        return deployed_named_contract

    def _get_abi_and_deployer_from_params(
        self,
        logging_contract_name: str,
        abi: str
        | Path
        | list
        | VyperDeployer
        | VyperContract
        | ZksyncContract
        | ZksyncDeployer
        | ABIContractFactory
        | ABIContract
        | None = None,
        abi_from_explorer: bool | None = None,
        address: str | None = None,
    ) -> Tuple[Union[list, None], Union[VyperDeployer, ZksyncDeployer, None]]:
        if abi_from_explorer and not address:
            raise ValueError(
                f"Cannot get ABI from explorer without an address for contract {logging_contract_name}. Please provide an address."
            )

        abi_like = abi
        abi = None
        deployer = None

        config = get_config()
        if abi_like:
            if isinstance(abi_like, str):
                # Check if it's a file path
                if abi_like.endswith(".json") or abi_like.endswith(".vyi"):
                    if abi_like.endswith(".json"):
                        abi_path = config.project_root.joinpath(abi_like)
                        abi = boa.load_abi(str(abi_path)).abi
                        abi = cast(list, abi)
                        return abi, deployer
                    elif abi_like.endswith(".vyi"):
                        raise NotImplementedError(
                            f"Loading an ABI from Vyper Interface files is not yet supported for contract {logging_contract_name}. You can track the progress here:\nhttps://github.com/vyperlang/vyper/issues/4232"
                        )
                else:
                    contract_path = config.find_contract(abi_like)
                    deployer = boa.load_partial(str(contract_path))
                    if isinstance(deployer, VyperDeployer):
                        abi = build_abi_output(deployer.compiler_data)
                    elif isinstance(deployer, ZksyncDeployer):
                        abi = deployer.zkvyper_data
                    abi = cast(list, abi)
                    return abi, deployer
            if isinstance(abi_like, list):
                # If its an ABI, just take it
                return abi_like, deployer
            if isinstance(abi_like, VyperDeployer) or isinstance(
                abi_like, ZksyncDeployer
            ):
                return build_abi_output(abi_like.compiler_data), abi_like
            if isinstance(abi_like, VyperContract) or isinstance(
                abi_like, ZksyncContract
            ):
                return abi_like.abi, abi_like.deployer
            if isinstance(abi_like, ABIContractFactory):
                return abi_like.abi, deployer
            if isinstance(abi_like, ABIContract):
                return abi_like.abi, deployer
        if abi_from_explorer:
            from moccasin.commands.explorer import boa_get_abi_from_explorer

            abi = boa_get_abi_from_explorer(str(address), quiet=True)
        return abi, deployer  # type: ignore


################################################################
#                        NETWORKS TOML                         #
################################################################
class _Networks:
    """
    Networks configuration held by the Moccasin TOML file

    @dev Here we can not export it to its own file since it
        depends on Network class and Config class. Maybe there
        is a better way to do it.
    """

    _networks: dict[str, Network]
    _default_named_contracts: dict[str, NamedContract]
    _overriden_active_network: Network | None
    default_db_path: Path
    default_network_name: str

    def __init__(self, toml_data: dict, project_root: Path):
        self._networks = {}
        self._default_named_contracts = {}
        self._overriden_active_network = None
        self.custom_networks_counter = 0
        project_data = toml_data.get("project", {})

        db_path_str = project_data.get("db_path", DB_PATH_LIVE_DEFAULT)
        db_path = Path(db_path_str).expanduser()
        if not db_path.is_absolute():
            db_path = project_root.joinpath(db_path)
        self.default_db_path = db_path

        default_explorer_api_key = project_data.get("explorer_api_key", None)
        default_explorer_uri = project_data.get("explorer_uri", None)
        default_explorer_type = project_data.get("explorer_type", None)
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
        toml_data = self._add_local_network_defaults(toml_data)
        for network_name, network_data in toml_data["networks"].items():
            # Check for restricted items for pyevm or eravm
            if network_name in [PYEVM, ERAVM]:
                self._validate_local_network_data(network_data, network_name)
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
                # Review: We might need to validate the named contracts against the actual names of contracts
                # So there is no collision
                if network_data.get("fork", None) is True:
                    network_data = self._add_fork_network_defaults(network_data)
                    self._validate_fork_network_defaults(network_data)
                network = Network(
                    name=network_name,
                    is_fork=network_data.get("fork", False),
                    url=network_data.get("url", None),
                    is_zksync=network_data.get("is_zksync", False),
                    chain_id=network_data.get("chain_id", None),
                    save_abi_path=network_data.get(
                        SAVE_ABI_PATH, default_save_abi_path
                    ),
                    explorer_uri=network_data.get("explorer_uri", default_explorer_uri),
                    explorer_api_key=network_data.get(
                        "explorer_api_key", default_explorer_api_key
                    ),
                    explorer_type=network_data.get(
                        "explorer_type", default_explorer_type
                    ),
                    default_account_name=network_data.get("default_account_name", None),
                    unsafe_password_file=network_data.get("unsafe_password_file", None),
                    prompt_live=network_data.get("prompt_live", True),
                    save_to_db=network_data.get(SAVE_TO_DB, True),
                    live_or_staging=network_data.get("live_or_staging", True),
                    db_path=network_data.get("db_path", self.default_db_path),
                    named_contracts=final_network_contracts,
                    extra_data=network_data.get("extra_data", {}),
                )
                setattr(self, network_name, network)
                self._networks[network_name] = network

    def __len__(self):
        return len(self._networks)

    def get_networks(self) -> dict[str, Network]:
        return self._networks

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
        if self._overriden_active_network is not None:
            return self._overriden_active_network
        if boa.env.nickname in self._networks:
            return self._networks[boa.env.nickname]
        new_network = Network(
            name=boa.env.nickname, named_contracts=self._default_named_contracts
        )
        self._networks[new_network.name] = new_network
        return new_network

    def get_default_db_path(self) -> Path:
        return self.default_db_path

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

    def get_or_deploy_named_contract(
        self, *args, **kwargs
    ) -> VyperContract | ZksyncContract | ABIContract:
        return self.get_active_network().get_or_deploy_named_contract(*args, **kwargs)

    def set_active_network(
        self, name_of_network_or_network: str | Network, activate_boa=True, **kwargs
    ) -> Network:
        if not isinstance(name_of_network_or_network, str) and not isinstance(
            name_of_network_or_network, Network
        ):
            raise ValueError(
                f"The first argument must be a string or a Network object, you gave {name_of_network_or_network}."
            )

        if isinstance(name_of_network_or_network, str):
            name_of_network_or_network = self.get_network(name_of_network_or_network)
            name_of_network_or_network = cast(Network, name_of_network_or_network)

        name_of_network_or_network.set_kwargs(**kwargs)
        if activate_boa:
            name_of_network_or_network.create_and_set_or_set_boa_env()
            self._overriden_active_network = None
        else:
            self._overriden_active_network = name_of_network_or_network
        if not name_of_network_or_network.is_local_or_forked_network():
            name_of_network_or_network._set_boa_db()
        self._networks[name_of_network_or_network.name] = name_of_network_or_network
        return name_of_network_or_network

    def activate_boa(self):
        active_network = self.get_active_network()
        active_network.create_and_set_or_set_boa_env()
        self._overriden_active_network = None

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

    @staticmethod
    def _add_local_network_defaults(toml_data: dict) -> dict:
        if "networks" not in toml_data:
            toml_data["networks"] = {}

        for local_network, local_network_data in LOCAL_NETWORK_DEFAULTS.items():
            if local_network not in toml_data["networks"]:
                toml_data["networks"][local_network] = {}

            for key, value in local_network_data.items():
                if toml_data["networks"][local_network].get(key, None) is None:
                    toml_data["networks"][local_network][key] = value
        return toml_data

    @staticmethod
    def _add_fork_network_defaults(network_data: dict) -> dict:
        network_data["prompt_live"] = network_data.get(
            "prompt_live", FORK_NETWORK_DEFAULTS["prompt_live"]
        )
        network_data[SAVE_TO_DB] = network_data.get(
            SAVE_TO_DB, FORK_NETWORK_DEFAULTS[SAVE_TO_DB]
        )
        network_data["live_or_staging"] = network_data.get(
            "live_or_staging", FORK_NETWORK_DEFAULTS["live_or_staging"]
        )
        return network_data

    @staticmethod
    def _validate_fork_network_defaults(network_data: dict):
        if network_data.get(SAVE_TO_DB, False) is True:
            raise ValueError(
                "You cannot save forked network data to a live database. Please set 'save_to_db' to 'False' or leave it unset."
            )

    @staticmethod
    def _validate_local_network_data(network_data: dict, network_name: str):
        for key in network_data.keys():
            if key in RESTRICTED_VALUES_FOR_LOCAL_NETWORK:
                raise ValueError(f"Cannot set {key} for network {network_name}.")
            if network_name == PYEVM:
                if network_data.get("is_zksync", False) is True:
                    raise ValueError(
                        f"is_zksync for {network_name} must be false. Please adjust it in your config."
                    )
            if network_name == ERAVM:
                if network_data.get("is_zksync", True) is False:
                    raise ValueError(
                        f"is_zksync for {network_name} must be True. Please adjust it in your config."
                    )
        for key in SPECIFIC_VALUES_FOR_ALL_LOCAL_NETWORKS.keys():
            if network_data.get(
                key, None
            ) != SPECIFIC_VALUES_FOR_ALL_LOCAL_NETWORKS.get(key, None):
                raise ValueError(
                    f"{key} for {network_name} must be {SPECIFIC_VALUES_FOR_ALL_LOCAL_NETWORKS[key]} or left unset. Please adjust it in your config."
                )


################################################################
#                            CONFIG                            #
################################################################
class Config:
    """A wrapper around the moccasin.toml file, it is also the main entry point for doing
    almost anything with moccasin.

    This class reads the moccasin.toml file and sets up project configuration.

    Attributes:
        _project_root (Path): The root directory of the project.
        _toml_data (dict): The raw data from moccasin.toml.
        dependencies (list[str]): Project dependencies from moccasin.toml.
        project (dict[str, str]): Project data from moccasin.toml.
        extra_data (dict[str, Any]): Any additional data from moccasin.toml.
        networks (_Networks): Network configurations.

    Args:
        root_path (Path, optional): The root directory of the project. Defaults to None.
    """

    _project_root: Path
    _toml_data: dict
    dependencies: list[str]
    project: dict[str, str]
    extra_data: dict[str, Any]
    networks: _Networks

    def __init__(self, root_path: Path | None):
        if root_path is None:
            root_path = Config.find_project_root()
        root_path = cast(Path, root_path)
        self._project_root = root_path
        self._toml_data = {}
        self.project = {}

        config_path: Path = root_path.joinpath(CONFIG_NAME)
        pyproject_path: Path = root_path.joinpath("pyproject.toml")

        if config_path.exists() or pyproject_path.exists():
            self._load_config(config_path, pyproject_path=pyproject_path)
        else:
            self._load_env_file()
            logger.warning(
                f"No {CONFIG_NAME} or pyproject.toml file found. Using default configuration."
            )
        self.networks = _Networks(self._toml_data, self.project_root)

    def _load_config(self, config_path: Path, pyproject_path: Path | None = None):
        toml_data = self.read_configs(config_path, pyproject_path)
        # Need to get the .env file before expanding env vars
        self.project[DOT_ENV_KEY] = toml_data.get("project", {}).get(
            DOT_ENV_KEY, DOT_ENV_FILE
        )
        self._load_env_file()
        toml_data = self.expand_env_vars(toml_data)
        self.dependencies = toml_data.get("project", {}).get("dependencies", [])
        self.project = toml_data.get("project", {})
        self.extra_data = toml_data.get("extra_data", {})
        self._toml_data = toml_data
        if TESTS_FOLDER in self.project:
            logger.warning(
                f"Tests folder is set to {self.project[TESTS_FOLDER]}. This is not supported and will be ignored."
            )

    def _load_env_file(self):
        load_dotenv(dotenv_path=self.project_root.joinpath(self.dot_env))

    def reload(self):
        self.__init__(self.project_root)

    def get_config_path(self) -> Path:
        return self.config_path

    def read_configs_preserve_comments(
        self,
        moccasin_config_path: Path | None = None,
        pyproject_config_path: Path | None = None,
    ) -> tomlkit.TOMLDocument:
        if moccasin_config_path is None:
            moccasin_config_path = self.config_path
        if pyproject_config_path is None:
            pyproject_config_path = self.project_root.joinpath("pyproject.toml")
        moccasin_config = self.read_moccasin_toml_preserve_comments(
            moccasin_config_path
        )
        pyproject_config = self.read_pyproject_toml_preserve_comments(
            pyproject_config_path
        )
        if moccasin_config == {}:
            return pyproject_config
        merged_config = self.merge_configs(moccasin_config, pyproject_config)
        merged_config = cast(tomlkit.TOMLDocument, merged_config)
        return merged_config

    def read_configs(
        self, moccasin_path: Path | None = None, pyproject_path: Path | None = None
    ) -> dict:
        moccasin_data = self.read_moccasin_config(moccasin_path)
        pyproject_data = self.read_pyproject_config(pyproject_path)
        return self.merge_configs(moccasin_data, pyproject_data)

    def read_moccasin_config(self, config_path: Path | None = None) -> dict:
        if config_path is None:
            config_path = self.config_path
        return self.read_moccasin_toml(config_path)

    def read_pyproject_config(self, pyproject_path: Path | None = None) -> dict:
        if pyproject_path is None:
            pyproject_path = self.project_root.joinpath("pyproject.toml")
        return self.read_pyproject_toml(pyproject_path)

    def expand_env_vars(self, value):
        if isinstance(value, str):
            return os.path.expandvars(value)
        elif isinstance(value, dict):
            return {k: self.expand_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.expand_env_vars(item) for item in value]
        return value

    def get_networks(self) -> dict[str, Network]:
        return self.networks.get_networks()

    def get_active_network(self) -> Network:
        return self.networks.get_active_network()

    def get_default_db_path(self) -> Path:
        return self.networks.get_default_db_path()

    def get_or_deploy_named_contract(
        self, *args, **kwargs
    ) -> VyperContract | ZksyncContract | ABIContract:
        return self.get_active_network().get_or_deploy_named_contract(*args, **kwargs)

    def get_dependencies(self) -> list[str]:
        return self.dependencies

    def write_dependencies(self, dependencies: list):
        """Writes the dependencies to the config file.

        If a moccasin.toml file exists, it will write there, otherwise, it'll write to pyproject.toml.

        This will overwrite the existing dependencies with the new ones. So if you wish to keep old ones,
        read from the dependencies first.
        """
        toml_data = self.read_configs_preserve_comments()
        path_to_write = self.config_path
        if not self.config_path.exists() and self.pyproject_path.exists():
            self.nested_tomlkit_update(
                toml_data, ["tool", "moccasin", "project", "dependencies"], dependencies
            )
            path_to_write = self.pyproject_path
        else:
            self.nested_tomlkit_update(
                toml_data, ["project", "dependencies"], dependencies
            )

        # Create a temporary file in the same directory as the target file
        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            dir=path_to_write.parent,
            prefix=".tmp_",
            suffix=".toml",
        )
        try:
            temp_file.write(tomlkit.dumps(toml_data))
            temp_file.close()
            shutil.move(temp_file.name, path_to_write)
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

    def find_contract(self, contract_or_contract_path: str) -> Path:
        return self._find_contract(
            self.project_root,
            self.contracts_folder,
            self.lib_folder,
            contract_or_contract_path,
        )

    def set_active_network(
        self, name_url_or_id: str | Network, activate_boa=True, **kwargs
    ) -> Network:
        return self.networks.set_active_network(
            name_url_or_id, activate_boa=activate_boa, **kwargs
        )

    def activate_boa(self):
        self.networks.activate_boa()

    @property
    def config_path(self) -> Path:
        return self.project_root.joinpath(CONFIG_NAME)

    @property
    def pyproject_path(self) -> Path:
        return self.project_root.joinpath("pyproject.toml")

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
        return self.networks.default_network_name

    @property
    def default_network_name(self) -> str:
        return self.default_network

    @staticmethod
    def load_config_from_root(project_root: Path | None = None) -> "Config":
        if project_root is None:
            project_root = Config.find_project_root()
        return Config(project_root)

    @staticmethod
    def find_project_root(start_path: Path | str | None = None) -> Path:
        if start_path is None:
            start_path = Path.cwd()
        start_path = Path(start_path).expanduser().resolve()
        current_path = start_path

        # Look for moccasin.toml
        while True:
            # Move up to the parent directory
            parent_path = current_path.parent
            if parent_path == current_path:
                # We've reached the root directory without finding moccasin.toml
                # raise FileNotFoundError(
                #     "Could not find moccasin.toml or src directory with Vyper contracts in any parent directory"
                # )
                break
            if (current_path / CONFIG_NAME).exists():
                return current_path
            # Check for src directory with .vy files in current directory
            src_path = current_path / "src"
            if src_path.is_dir() and any(src_path.glob("*.vy")):
                return current_path
            current_path = parent_path

        # Start over and look for pyproject.toml
        current_path = start_path
        while True:
            # Move up to the parent directory
            parent_path = current_path.parent
            if parent_path == current_path:
                # We've reached the root directory without finding moccasin.toml
                raise FileNotFoundError(
                    "Could not find moccasin.toml, pyproject.toml, or src directory with Vyper contracts in any parent directory"
                )
            if (current_path / "pyproject.toml").exists():
                return current_path
            current_path = parent_path

    @staticmethod
    def read_moccasin_toml(config_path: Path) -> dict:
        if not config_path.exists():
            return {}
        with open(config_path, "rb") as f:
            return tomllib.load(f)

    @staticmethod
    def read_moccasin_toml_preserve_comments(config_path: Path) -> tomlkit.TOMLDocument:
        config_path = Config._validated_moccasin_config_path(config_path)
        if not config_path.exists():
            return tomlkit.TOMLDocument()
        with open(config_path, "rb") as f:
            return tomlkit.load(f)

    @staticmethod
    def read_pyproject_toml_preserve_comments(
        config_path: Path,
    ) -> tomlkit.TOMLDocument:
        config_path = Config._validated_pyproject_config_path(config_path)
        if not config_path.exists():
            return tomlkit.TOMLDocument()
        with open(config_path, "rb") as f:
            return tomlkit.load(f)

    @staticmethod
    def read_pyproject_toml(pyproject_path: Path) -> dict:
        if not pyproject_path.exists():
            return {}

        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)

        pyproject_config_toml = pyproject_data.get("tool", {}).get("moccasin", {})
        return pyproject_config_toml

    @staticmethod
    def merge_configs(
        moccasin_config_dict: Union[dict, tomlkit.TOMLDocument],
        pyproject_config_dict: Union[dict, tomlkit.TOMLDocument],
    ) -> Union[dict, tomlkit.TOMLDocument]:
        merged = moccasin_config_dict.copy()

        if (
            pyproject_config_dict.get("tool", {})
            .get("moccasin", {})
            .get("project", {})
            .get("dependencies", None)
            is not None
        ):
            logger.warning(
                "Dependencies in pyproject.toml will be overwritten by dependencies in moccasin.toml if the moccasin.toml has dependencies!"
            )

        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict):
                    if k not in d:
                        d[k] = {}
                    deep_update(d[k], v)
                elif k not in d:
                    d[k] = v
            return d

        return deep_update(merged, pyproject_config_dict)

    @staticmethod
    def _validated_pyproject_config_path(config_path: Path):
        if not str(config_path).endswith("pyproject.toml"):
            config_path = config_path.joinpath("pyproject.toml")
        return config_path

    @staticmethod
    def _validated_moccasin_config_path(config_path: Path):
        if not str(config_path).endswith("moccasin.toml"):
            config_path = config_path.joinpath("moccasin.toml")
        return config_path

    @staticmethod
    def nested_tomlkit_update(
        toml_data: tomlkit.TOMLDocument,
        keys: list,
        value: str | int | float | bool | list | dict,
    ) -> tomlkit.TOMLDocument:
        current: Union[tomlkit.TOMLDocument, Table] = toml_data
        for key in keys[:-1]:
            if key not in current:
                current[key] = tomlkit.table()
            current = current[key]  # type: ignore
        current[keys[-1]] = value
        return toml_data

    @staticmethod
    def _find_contract(
        project_root: str | Path,
        contracts_folder: str,
        lib_folder: str,
        contract_or_contract_path: str,
    ) -> Path:
        project_root = Path(project_root)
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
            contract_path = project_root / contract_path
            if contract_path.exists():
                return contract_path

        # Search for the contract in the contracts folder if not found by now
        contracts_location = project_root / contracts_folder
        contract_paths = list(contracts_location.rglob(contract_path.name))

        if not contract_paths:
            # We will try the lib folder
            contracts_location = project_root / lib_folder
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


################################################################
#                        CONFIG HELPERS                        #
################################################################
_config: Config | None = None


def get_active_network() -> Network:
    return get_config().get_active_network()


# REVIEW: Do we need... all of these?
def get_or_initialize_config(config_path: Path | None = None) -> Config:
    global _config
    if _config is None:
        _config = initialize_global_config(config_path)
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
    _set_global_config(config_path)
    return get_config()


def _set_global_config(config_path: Path | None = None) -> Config:
    global _config
    _config = Config.load_config_from_root(config_path)
    return _config
