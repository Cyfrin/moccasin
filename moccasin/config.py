import os
import shutil
import tempfile
import tomllib
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Optional, Union, cast

import boa
import tomlkit
from boa.contracts.abi.abi_contract import ABIContract, ABIContractFactory
from boa.contracts.vyper.vyper_contract import VyperContract, VyperDeployer
from boa.deployments import Deployment, get_deployments_db
from boa.environment import Env
from boa.util.abi import Address
from boa.verifiers import get_verification_bundle
from boa_zksync import set_zksync_env, set_zksync_fork, set_zksync_test_env

# REVIEW: Could/should these be optionally imported?
from boa_zksync.contract import ZksyncContract
from boa_zksync.deployer import ZksyncDeployer
from dotenv import load_dotenv
from eth_utils import to_hex

from moccasin.constants.vars import (
    BUILD_FOLDER,
    CONFIG_NAME,
    CONTRACTS_FOLDER,
    DB_PATH_LIVE_DEFAULT,
    DB_PATH_LOCAL_DEFAULT,
    DEFAULT_NETWORK,
    DEPENDENCIES_FOLDER,
    DOT_ENV_FILE,
    DOT_ENV_KEY,
    ERAVM,
    GET_CONTRACT_SQL,
    PYEVM,
    RESTRICTED_VALUES_FOR_LOCAL_NETWORK,
    SAVE_ABI_PATH,
    SAVE_TO_DB,
    SCRIPT_FOLDER,
    TESTS_FOLDER,
)
from moccasin.logging import logger
from moccasin.moccasin_account import MoccasinAccount
from moccasin.named_contract import NamedContract

if TYPE_CHECKING:
    from boa.network import NetworkEnv
    from boa.verifiers import Blockscout, VerificationResult
    from boa_zksync import ZksyncEnv
    from boa_zksync.verifiers import ZksyncExplorer

_AnyEnv = Union["NetworkEnv", "Env", "ZksyncEnv"]
VERIFIERS = Union["Blockscout", "ZksyncExplorer"]


@dataclass
class Network:
    name: str
    url: str | None = None
    chain_id: int | None = None
    is_fork: bool = False
    is_zksync: bool = False
    default_account_name: str | None = None
    unsafe_password_file: Path | None = None
    save_abi_path: str | None = None
    explorer_uri: str | None = None
    explorer_api_key: str | None = None
    explorer_type: str | None = None
    contracts: dict[str, NamedContract] = field(default_factory=dict)
    prompt_live: bool = True
    save_to_db: bool = True
    db_path: str | Path = DB_PATH_LOCAL_DEFAULT
    extra_data: dict[str, Any] = field(default_factory=dict)
    _network_env: _AnyEnv | None = None

    def _set_boa_env_and_db(self) -> _AnyEnv:
        """Sets the boa.env to the current network, this additionally sets up the database."""
        # perf: save time on imports in the (common) case where
        # we just import config for its utils but don't actually need
        # to switch networks
        from boa.deployments import DeploymentsDB, set_deployments_db
        from boa.network import EthereumRPC, NetworkEnv

        # 0. Set the database
        # The local networks should be validated at this point
        db: DeploymentsDB
        if self.save_to_db:
            db = DeploymentsDB(path=self.db_path)
        else:
            db = DeploymentsDB(path=DB_PATH_LOCAL_DEFAULT)
        set_deployments_db(db)

        # 1. Check for forking, and set (You cannot fork from a NetworkEnv, only a "new" Env!)
        if self.is_fork:
            if self.is_zksync:
                set_zksync_fork(url=self.url)
            else:
                boa.fork(self.url)

        # 2. Non-forked local networks
        elif self.name == PYEVM:
            env = Env()
            boa.set_env(env)
        elif self.name == ERAVM:
            set_zksync_test_env()

        # 3. Finally, "true" networks
        elif self.is_zksync:
            if self.explorer_type != "zksyncexplorer":
                logger.warning(
                    "Explorer type is not zksyncexplorer, as of today, only the zksync explorer is supported with zksync."
                )
            set_zksync_env(self.url, explorer_url=self.explorer_uri, nickname=self.name)
        else:
            env = NetworkEnv(EthereumRPC(self.url), nickname=self.name)
            boa.set_env(env)

        # 4. Quick sanity check on chain_id
        if not self.is_local_or_forked_network():
            expected_chain_id = boa.env.get_chain_id()  # type: ignore
            if self.chain_id and self.chain_id != expected_chain_id:
                raise ValueError(
                    f"Chain ID mismatch. Expected {expected_chain_id}, but user placed {self.chain_id} in their {CONFIG_NAME}."
                )
            self.chain_id = expected_chain_id if not self.chain_id else self.chain_id

            # 5. Set the explorer type and uri if not set by default ones
            if self.chain_id is not None and (
                self.explorer_uri is None or self.explorer_uri is None
            ):
                # Review: Is this down here even good?
                from moccasin.constants.vars import DEFAULT_NETWORKS_BY_CHAIN_ID

                default_network_info = DEFAULT_NETWORKS_BY_CHAIN_ID.get(
                    self.chain_id, {}
                )
                self.explorer_uri = (
                    self.explorer_uri
                    if self.explorer_uri is not None
                    else default_network_info.get("explorer", None)
                )
                self.explorer_type = (
                    self.explorer_type
                    if self.explorer_type is not None
                    else default_network_info.get("explorer_type", None)
                )

        boa.env.nickname = self.name
        return boa.env

    def moccasin_verify(
        self, contract: VyperContract | ZksyncContract
    ) -> "VerificationResult":
        """Verifies a contract using your moccasin.toml config."""
        verifier_class = self.get_verifier_class()
        verifier_instance = verifier_class(self.explorer_uri, self.explorer_api_key)
        if self.is_zksync:
            import boa_zksync

            return boa_zksync.verify(contract, verifier_instance)
        return boa.verify(contract, verifier_instance)

    def get_verifier_class(self) -> Any:
        if self.explorer_type is None:
            if self.explorer_uri is not None:
                if "blockscout" in self.explorer_uri:
                    self.explorer_type = "blockscout"
                elif "zksync" in self.explorer_uri:
                    self.explorer_type = "zksyncexplorer"

        if self.explorer_type is None:
            raise ValueError(
                f"No explorer type found. Please set the explorer_type in your {CONFIG_NAME}."
            )
        if self.explorer_uri is None:
            raise ValueError(
                f"No explorer_uri found. Please set the `explorer_uri` in your {CONFIG_NAME}."
            )

        verifier_name = self._to_verifier_name(self.explorer_type)
        from importlib import import_module

        module = import_module("moccasin.supported_verifiers")
        return getattr(module, verifier_name)

    def _to_verifier_name(self, verifier_string: str) -> str:
        if verifier_string.lower().strip() == "blockscout":
            return "Blockscout"
        if verifier_string.lower().strip() == "zksyncexplorer":
            return "ZksyncExplorer"
        raise ValueError(
            f"Verifier {verifier_string} is not supported. Please use 'blockscout' or 'zksyncexplorer'."
        )

    def get_default_account(self) -> MoccasinAccount | Any:
        """Returns an 'account-like' object."""
        if hasattr(boa.env, "_accounts"):
            if boa.env.eoa is not None:
                return boa.env._accounts[boa.env.eoa]
        else:
            if boa.env.eoa is not None:
                return MoccasinAccount(address=boa.env.eoa, ignore_warning=True)
        if (
            self.default_account_name is not None
            and self.unsafe_password_file is not None
        ):
            return MoccasinAccount(
                keystore_path_or_account_name=self.default_account_name,
                password_file_path=self.unsafe_password_file,
            )
        return None

    def create_and_set_or_set_boa_env(self, **kwargs) -> _AnyEnv:
        for key, value in kwargs.items():
            if value is not None:
                setattr(self, key, value)

        # REVIEW: Performance improvement. We don't need to create a new env if the kwargs are the same.
        # Potentially unnecessary
        if self.kwargs_are_different(**kwargs) or self._network_env is None:
            self._set_boa_env_and_db()
        self._network_env = boa.env
        return self._network_env

    def _fetch_contracts_from_db(
        self,
        contract_name: str,
        chain_id: int | str | None = None,
        limit: int | None = None,
    ) -> Iterator[Deployment]:
        limit_str = ""
        if limit is not None:
            limit_str = f"LIMIT {limit};"
        db = get_deployments_db()
        if db is None or not self.save_to_db:
            raise ValueError(
                f"The database is either not set, or save_to_db is false for network {self.name}."
            )
        field_names = db._get_fieldnames_str()
        if chain_id is None:
            chain_id = to_hex(self.chain_id)
        else:
            chain_id = to_hex(chain_id)
        final_sql = GET_CONTRACT_SQL.format(
            field_names, "'" + contract_name + "'", chain_id, limit_str
        )
        return db._get_deployments_from_sql(final_sql)

    def has_matching_integrity(
        self, deployment: Deployment, contract_name: str, config: "Config" = None
    ):
        vyper_deployer = self._get_deployer_from_contract_name(contract_name, config)
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

    def _get_deployer_from_contract_name(
        self, contract_name: str, config: Optional["Config"] = None
    ) -> VyperDeployer | ZksyncDeployer:
        if not config:
            config = get_config()
        contract_path = config._find_contract(contract_name)
        return boa.load_partial(str(contract_path.absolute()))

    def get_deployments_unchecked(
        self,
        contract_name: str,
        chain_id: int | str | None = None,
        limit: int | None = None,
    ) -> list[Deployment]:
        deployments_iter = self._fetch_contracts_from_db(
            contract_name, chain_id, limit=limit
        )
        return list(deployments_iter)

    def get_deployments_checked(
        self,
        contract_name: str,
        chain_id: int | str | None = None,
        limit: int | None = None,
    ) -> list[Deployment]:
        deployments_iter = self._fetch_contracts_from_db(
            contract_name, chain_id, limit=limit
        )
        deployments_list = []
        for deployment in deployments_iter:
            if self.has_matching_integrity(deployment, contract_name):
                deployments_list.append(deployment)
        return deployments_list

    def get_latest_deployment_checked(
        self,
        contract_name: str,
        chain_id: int | str | None = None,
        config: Optional["Config"] = None,
    ) -> Deployment | None:
        """Gets a deployment from the database, and checks the integrity hash."""
        deployments = self.get_deployments_checked(contract_name, chain_id, limit=1)
        if len(deployments) == 0:
            return None
        return deployments[0]

    def get_latest_deployment_unchecked(
        self, contract_name: str, chain_id: int | str | None = None
    ) -> Deployment | None:
        deployments = self.get_deployments_unchecked(contract_name, chain_id)
        if len(deployments) == 0:
            return None
        return deployments[0]

    def get_latest_contract_unchecked(
        self, contract_name: str, chain_id: int | str | None = None
    ) -> ABIContract | None:
        deployment = self.get_latest_deployment_unchecked(contract_name, chain_id)
        if deployment is not None:
            return self._convert_deployment_to_contract(deployment)
        return None

    def get_latest_contract_checked(
        self,
        contract_name: str,
        chain_id: int | str | None = None,
        config: Optional["Config"] = None,
    ) -> ABIContract | None:
        deployment = self.get_latest_deployment_checked(
            contract_name, chain_id, config=config
        )
        if deployment is not None:
            return self._convert_deployment_to_contract(deployment)
        return None

    def manifest_contract(
        self,
        contract_name: str,
        force_deploy: bool = False,
        address: str | None = None,
        checked: bool = False,
    ) -> VyperContract | ZksyncContract | ABIContract:
        """A wrapper around get_or_deploy_contract that is more explicit about the contract being deployed."""
        return self.get_or_deploy_contract(
            contract_name=contract_name,
            force_deploy=force_deploy,
            address=address,
            checked=checked,
        )

    def instantiate_contract(
        self, *args, **kwargs
    ) -> VyperContract | ZksyncContract | ABIContract:
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
        | ZksyncContract
        | ZksyncDeployer
        | ABIContractFactory
        | ABIContract
        | None = None,
        abi_from_explorer: bool | None = None,
        deployer_script: str | Path | None = None,
        address: str | None = None,
        checked: bool = False,
    ) -> VyperContract | ZksyncContract | ABIContract:
        """Returns or deploys a VyperContract, ZksyncContract, or ABIContract based on the name and address in the config file, or passed to this function.

        The following arguments are mutually exclusive:
            - abi
            - abi_from_explorer

        Args:
            - contract_name: the contract name or deployer for the contract.
            - force_deploy: if True, will deploy the contract even if the contract has an address in the config file.
            - abi: the ABI of the contract. Can be a list, string path to file, string of the ABI, VyperDeployer, VyperContract, ZksyncDeployer, ZksyncContract, ABIContractFactory, or ABIContract.
            - abi_from_explorer: if True, will fetch the ABI from the explorer.
            - deployer_script: If no address is given, this is the path to deploy the contract.
            - address: The address of the contract.

        Returns:
            VyperContract | ZksyncContract | ABIContract: The deployed contract instance, or a blank contract if the contract is not found.
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
                    f"Contract {named_contract.contract_name} has force_deploy=True but no deployer_script specified in their {CONFIG_NAME}."
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
        # We don't need to check the DB since we are checking the address on this network
        if (
            named_contract.abi == abi
            and named_contract.address == address
            and named_contract.vyper_contract
        ):
            return named_contract.vyper_contract

        # 4. Happy path, we check for this contract in the DB
        if self.chain_id is not None and self.save_to_db is True:
            vyper_contract: ABIContract | None = None
            if checked:
                vyper_contract = self.get_latest_contract_checked(
                    named_contract.contract_name
                )
            else:
                vyper_contract = self.get_latest_contract_unchecked(
                    named_contract.contract_name
                )
            if vyper_contract is not None:
                return vyper_contract

        # 5. Happy path, maybe we didn't deploy the contract, but we've been given an abi and address, which works
        if abi and address:
            if isinstance(abi, VyperDeployer) or isinstance(abi, ZksyncDeployer):
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
            blank_contract: VyperDeployer | ZksyncDeployer = boa.loads_partial("")
            vyper_contract = blank_contract.at(address)
            named_contract.update_from_deployed_contract(vyper_contract)
            self.contracts[named_contract.contract_name] = named_contract
            return vyper_contract

        # 6. If no address, deploy the contract
        if not deployer_script:
            raise ValueError(
                f"Contract {named_contract.contract_name} has no address or deployer_script specified in the {CONFIG_NAME}."
            )

        return self._deploy_named_contract(named_contract, deployer_script)

    def is_local_or_forked_network(self) -> bool:
        """Returns True if network is:
        1. pyevm
        2. eravm
        3. A fork
        """
        return self.name in [PYEVM, ERAVM] or self.is_fork

    def has_explorer(self) -> bool:
        return self.explorer_uri is not None

    def _deploy_named_contract(
        self, named_contract: NamedContract, deployer_script: str | Path
    ) -> VyperContract | ZksyncContract:
        config = get_config()
        deployed_named_contract: VyperContract | ZksyncContract = (
            named_contract._deploy(
                config.script_folder, deployer_script, update_from_deploy=True
            )
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
        | ZksyncContract
        | ZksyncDeployer
        | ABIContractFactory
        | ABIContract
        | None = None,
        abi_from_explorer: bool | None = None,
        address: str | None = None,
    ) -> str | VyperDeployer | ZksyncDeployer | None:
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
            if isinstance(abi, VyperDeployer) or isinstance(abi, ZksyncDeployer):
                return abi
            if isinstance(abi, VyperContract) or isinstance(abi, ZksyncContract):
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

    def kwargs_are_different(self, **kwargs) -> bool:
        for key, value in kwargs.items():
            if getattr(self, key, None) != value:
                return True
        return False

    def set_boa_eoa(self, account: MoccasinAccount):
        if self.is_local_or_forked_network:  # type: ignore[truthy-function]
            boa.env.eoa = Address(account.address)
        else:
            boa.env.add_account(account, force_eoa=True)

    @property
    def alias(self) -> str:
        return self.name

    @property
    def identifier(self) -> str:
        return self.name

    @staticmethod
    def _convert_deployment_to_contract(deployment: Deployment) -> ABIContract:
        contract_factory = ABIContractFactory(
            deployment.contract_name,
            deployment.abi,
            deployment.contract_name + "_" + deployment.source_code["integrity"],
        )
        return contract_factory.at(deployment.contract_address)


class _Networks:
    _networks: dict[str, Network]
    _default_named_contracts: dict[str, NamedContract]
    db_path: Path
    default_network_name: str

    def __init__(self, toml_data: dict, db_path: Path):
        self._networks = {}
        self._default_named_contracts = {}
        self.custom_networks_counter = 0
        self.db_path = db_path
        project_data = toml_data.get("project", {})

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
                    db_path=self.db_path,
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

    def get_db_path(self) -> Path:
        return self.db_path

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

    def get_or_deploy_contract(
        self, *args, **kwargs
    ) -> VyperContract | ZksyncContract | ABIContract:
        return self.get_active_network().get_or_deploy_contract(*args, **kwargs)

    def set_active_network(self, name_of_network_or_network: str | Network, **kwargs):
        if not isinstance(name_of_network_or_network, str) and not isinstance(
            name_of_network_or_network, Network
        ):
            raise ValueError(
                f"The first argument must be a string or a Network object, you gave {name_of_network_or_network}."
            )

        if isinstance(name_of_network_or_network, str):
            name_of_network_or_network = self.get_network(name_of_network_or_network)
            name_of_network_or_network = cast(Network, name_of_network_or_network)

        name_of_network_or_network.create_and_set_or_set_boa_env(**kwargs)
        self._networks[name_of_network_or_network.name] = name_of_network_or_network

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

    @staticmethod
    def _add_local_network_defaults(toml_data: dict) -> dict:
        if "networks" not in toml_data:
            toml_data["networks"] = {}

        # Define default values for PYEVM and ERAVM
        local_networks_defaults = {
            PYEVM: {"is_zksync": False, "prompt_live": False, SAVE_TO_DB: False},
            ERAVM: {"is_zksync": True, "prompt_live": False, SAVE_TO_DB: False},
        }

        for local_network, local_network_data in local_networks_defaults.items():
            if local_network not in toml_data["networks"]:
                toml_data["networks"][local_network] = {}

            for key, value in local_network_data.items():
                if toml_data["networks"][local_network].get(key, None) is None:
                    toml_data["networks"][local_network][key] = value
        return toml_data

    @staticmethod
    def _add_fork_network_defaults(network_data: dict) -> dict:
        network_data["prompt_live"] = network_data.get("prompt_live", False)
        network_data[SAVE_TO_DB] = network_data.get(SAVE_TO_DB, False)
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
            if network_data.get(SAVE_TO_DB) is True:
                raise ValueError(
                    f"{SAVE_TO_DB} for {network_name} must be 'False' or left unset. Please adjust it in your config."
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
        self.dependencies = toml_data.get("project", {}).get("dependencies", [])
        self.project = toml_data.get("project", {})

        # Setup networks and the database for deployments
        # Review, we could probably skip this if the active network is local...
        db_path_str = toml_data.get("project", {}).get("db_path", DB_PATH_LIVE_DEFAULT)
        db_path = Path(db_path_str).expanduser()
        if not db_path.is_absolute():
            db_path = self._project_root.joinpath(db_path)
        self.networks = _Networks(toml_data, db_path)

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
            raise FileNotFoundError(f"{CONFIG_NAME} not found: {config_path}")
        return config_path

    def expand_env_vars(self, value):
        if isinstance(value, str):
            return os.path.expandvars(value)
        elif isinstance(value, dict):
            return {k: self.expand_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.expand_env_vars(item) for item in value]
        return value

    def get_active_network(self) -> Network:
        return self.networks.get_active_network()

    def get_db_path(self) -> Path:
        return self.networks.get_db_path()

    def get_or_deploy_contract(
        self, *args, **kwargs
    ) -> VyperContract | ZksyncContract | ABIContract:
        return self.get_active_network().get_or_deploy_contract(*args, **kwargs)

    def get_dependencies(self) -> list[str]:
        return self.dependencies

    def write_dependencies(self, dependencies: list):
        """Writes the dependencies to the config file.

        This will overwrite the existing dependencies with the new ones. So if you wish to keep old ones,
        read from the dependencies first.
        """
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
        return self.networks.default_network_name

    @property
    def default_network_name(self) -> str:
        return self.default_network

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


def get_active_network() -> Network:
    return get_config().get_active_network()


def initialize_global_config(config_path: Path | None = None) -> Config:
    global _config
    assert _config is None
    _set_config(config_path)
    return get_config()


def _set_config(config_path: Path | None = None) -> Config:
    global _config
    _config = Config.load_config_from_path(config_path)
    return _config
