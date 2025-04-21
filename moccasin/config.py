import os
import shutil
import tempfile
import tomllib
import warnings
from dataclasses import dataclass, field
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
from boa.deployments import (
    Deployment,
    DeploymentsDB,
    get_deployments_db,
    set_deployments_db,
)
from boa.environment import Env
from boa.util.abi import Address
from boa.verifiers import get_verification_bundle
from boa_zksync import set_zksync_env, set_zksync_fork, set_zksync_test_env
from boa_zksync.contract import ZksyncContract
from boa_zksync.deployer import ZksyncDeployer
from dotenv import load_dotenv
from eth_utils import to_hex
from tomlkit.items import Table

from moccasin.constants.chains import ETHERSCAN_EXPLORERS
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
    FORK_NETWORK_DEFAULTS,
    GET_CONTRACT_SQL,
    LOCAL_NETWORK_DEFAULTS,
    PYEVM,
    RESTRICTED_VALUES_FOR_LOCAL_NETWORK,
    SAVE_ABI_PATH,
    SAVE_TO_DB,
    SCRIPT_FOLDER,
    SPECIFIC_VALUES_FOR_ALL_LOCAL_NETWORKS,
    SQL_AND,
    SQL_CHAIN_ID,
    SQL_CONTRACT_NAME,
    SQL_LIMIT,
    SQL_WHERE,
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
    """Represents a Moccasin network configuration from the ``moccasin.toml`` file settings.

    This class allows for flexible network configuration across different blockchain environments,
    supporting both local and remote networks, including special cases like forked networks.

    :param name: Unique identifier for the network
    :type name: str
    :param url: Network endpoint URL
    :type url: str | None
    :param chain_id: Unique identifier for the blockchain network
    :type chain_id: int | None
    :param is_fork: Indicates if the network is a forked instance
    :type is_fork: bool
    :param block_identifier: Block identifier for the network
    :type block_identifier: int | str
    :param is_zksync: Indicates if the network is a zkSync network
    :type is_zksync: bool
    :param default_account_name: Default mox wallet account name to use for the network
    :type default_account_name: str | None
    :param unsafe_password_file: Path to the unsafe password file related to ``default_account_name``
    :type unsafe_password_file: Path | None
    :param save_abi_path: Path to save the ABI
    :type save_abi_path: str | None
    :param explorer_uri: URI of the explorer
    :type explorer_uri: str | None
    :param explorer_api_key: API key for the explorer
    :type explorer_api_key: str | None
    :param explorer_type: Type of the explorer ("blockscout", "etherscan", "zksyncexplorer")
    :type explorer_type: str | None
    :param named_contracts: Dictionary of named contracts
    :type named_contracts: dict[str, NamedContract]
    :param prompt_live: A flag that will prompt you before sending a transaction, it defaults to true for "non-testing" networks
    :type prompt_live: bool
    :param save_to_db: Indicates if the network should save the deployment to the database, it defaults to true for "non-testing" networks
    :type save_to_db: bool
    :param live_or_staging: Indicates if the network is live or staging, defaults to true for non-local, non-forked networks
    :type live_or_staging: bool
    :param db_path: Path to the database
    :type db_path: str | Path
    :param extra_data: Extra data for the network
    :type extra_data: dict[str, Any]
    :param _network_env: Network environment
    :type _network_env: _AnyEnv | None
    """

    name: str
    url: str | None = None
    chain_id: int | None = None
    is_fork: bool = False
    block_identifier: int | str = "safe"
    is_zksync: bool = False
    default_account_name: str | None = None
    unsafe_password_file: Path | None = None
    save_abi_path: str | None = None
    explorer_uri: str | None = None
    explorer_api_key: str | None = None
    explorer_type: str | None = None
    named_contracts: dict[str, NamedContract] = field(default_factory=dict)
    prompt_live: bool = True
    save_to_db: bool = True
    live_or_staging: bool = True
    db_path: str | Path = DB_PATH_LOCAL_DEFAULT
    extra_data: dict[str, Any] = field(default_factory=dict)
    _network_env: _AnyEnv | None = None

    def _set_boa_env(self) -> _AnyEnv:
        """Sets the boa.env to the current network, this additionally sets up the database.

        :return: The boa.env
        """
        # perf: save time on imports in the (common) case where
        # we just import config for its utils but don't actually need
        # to switch networks
        from boa.network import EthereumRPC, NetworkEnv

        # 1. Check for forking, and set (You cannot fork from a NetworkEnv, only a "new" Env!)
        if self.is_fork:
            if self.is_zksync:
                set_zksync_fork(url=self.url, block_identifier=self.block_identifier)
            else:
                boa.fork(self.url, block_identifier=self.block_identifier)

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
        """Verifies a contract using your moccasin.toml config.

        :param contract: The contract to verify
        :type contract: VyperContract | ZksyncContract
        :return: The verification result of the contract
        :rtype: VerificationResult
        """
        verifier_class = self.get_verifier_class()
        verifier_instance = verifier_class(self.explorer_uri, self.explorer_api_key)
        if self.is_zksync:
            import boa_zksync

            return boa_zksync.verify(contract, verifier_instance)
        return boa.verify(contract, verifier_instance)

    def is_matching_boa(self) -> bool:
        """Checks if the current network is the active network in boa.

        This is a good way to test if you've overriden boa as the "active" network.

        :return: True if the current network is the active network in boa
        :rtype: bool
        """
        return boa.env.nickname == self.name

    def get_verifier_class(self) -> Any:
        """Returns the verifier class based on the explorer type.

        :return: The verifier class
        :rtype: Any
        """
        if self.explorer_type is None:
            if self.explorer_uri is not None:
                if "blockscout" in self.explorer_uri:
                    self.explorer_type = "blockscout"
                elif "zksync" in self.explorer_uri:
                    self.explorer_type = "zksyncexplorer"
                elif self.explorer_uri.strip('/') in ETHERSCAN_EXPLORERS.keys():
                    self.explorer_type = "etherscan"

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
        """Converts a verifier string to a verifier name.

        :param verifier_string: The verifier string
        :type verifier_string: str
        :return: The verifier name
        :rtype: str
        """
        if verifier_string.lower().strip() == "blockscout":
            return "Blockscout"
        if verifier_string.lower().strip() == "zksyncexplorer":
            return "ZksyncExplorer"
        if verifier_string.lower().strip() == "etherscan":
            return "Etherscan"
        raise ValueError(
            f"Verifier {verifier_string} is not supported. Please use 'blockscout', 'etherscan' or 'zksyncexplorer'."
        )

    def get_default_account(self) -> MoccasinAccount | Any:
        """Returns an 'account-like' object.

        :return: An 'account-like' object
        :rtype: MoccasinAccount | Any
        """
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

    def set_kwargs(self, **kwargs):
        """Sets the kwargs.

        :param kwargs: The kwargs
        :type kwargs: dict
        """
        for key, value in kwargs.items():
            if value is not None:
                setattr(self, key, value)

    def _set_boa_db(self) -> None:
        """Sets the boa deployments db."""
        db: DeploymentsDB
        if self.save_to_db:
            db = DeploymentsDB(path=self.db_path)
        else:
            db = DeploymentsDB(path=DB_PATH_LOCAL_DEFAULT)
        set_deployments_db(db)

    def create_and_set_or_set_boa_env(self, **kwargs) -> _AnyEnv:
        """Creates and sets the boa environment.

        :param kwargs: The kwargs
        :type kwargs: dict
        :return: The boa environment
        :rtype: _AnyEnv
        """
        self.set_kwargs(**kwargs)
        self._set_boa_env()
        self._network_env = boa.env
        return self._network_env

    def _generate_sql_from_args(
        self,
        contract_name: str | None = None,
        chain_id: int | str | None = None,
        limit: int | None = None,
        db: DeploymentsDB | None = None,
    ) -> tuple[str, tuple]:
        """Generates the SQL query from the args to fetch deployments from the db.

        :param contract_name: The contract name
        :type contract_name: str | None
        :param chain_id: The chain ID
        :type chain_id: int | str | None
        :param limit: The limit
        :type limit: int | None
        :param db: The db
        :type db: DeploymentsDB | None
        :return: The SQL query
        :rtype: str
        """
        if db is None:
            db = get_deployments_db()

        where_clauses = []
        params: list[str | int] = []

        field_names = db._get_fieldnames_str()

        if contract_name is not None:
            where_clauses.append(SQL_CONTRACT_NAME)
            params.append(contract_name)

        # Add chain_id condition if provided
        if chain_id is not None:
            where_clause = SQL_CHAIN_ID
            if where_clauses:
                where_clause = SQL_AND + where_clause
            where_clauses.append(where_clause)
            params.append(str(chain_id))

        where_part = ""
        if where_clauses:
            where_part = SQL_WHERE + "".join(where_clauses)

        # Add LIMIT if provided
        limit_part = ""
        if limit is not None:
            limit_part = SQL_LIMIT
            params.append(int(limit))

        sql_query = GET_CONTRACT_SQL.format(field_names, where_part, limit_part)
        return sql_query, tuple(params)

    def _fetch_deployments_from_db(
        self,
        contract_name: str | None = None,
        chain_id: int | str | None = None,
        limit: int | None = None,
        db: DeploymentsDB | None = None,
    ) -> Iterator[Deployment]:
        """Fetches deployments from the db with the given args.

        :param contract_name: The contract name
        :type contract_name: str | None
        :param chain_id: The chain ID
        :type chain_id: int | str | None
        :param limit: The limit
        :type limit: int | None
        :param db: The db
        :type db: DeploymentsDB | None
        :return: The deployments requested from the db
        :rtype: Iterator[Deployment]
        """
        if db is None:
            db = get_deployments_db()
        chain_id = to_hex(chain_id) if chain_id is not None else None
        if not isinstance(limit, int) and not isinstance(limit, type(None)):
            raise ValueError(f"Limit must be an integer, not {type(limit)}.")
        final_sql, params = self._generate_sql_from_args(
            contract_name=contract_name, chain_id=chain_id, limit=limit, db=db
        )
        return db._get_deployments_from_sql(final_sql, params)

    def _get_deployments_iterator(
        self,
        contract_name: str | None = None,
        chain_id: int | str | None = None,
        limit: int | None = None,
        config_or_db_path: Union["Config", Path, str, None] = None,
    ) -> Iterator[Deployment]:
        """Private method to get deployments from the database without an initialized config.

        :param contract_name: The contract name
        :type contract_name: str | None
        :param chain_id: The chain ID
        :type chain_id: int | str | None
        :param limit: The limit
        :type limit: int | None
        :param config_or_db_path: The config or db path
        :type config_or_db_path: Union[Config, Path, str, None]
        :return: The deployments iterator without an initialized config
        :rtype: Iterator[Deployment]
        """
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
        """Get deployments from the database without an initialized config.

        This method does not check if the deployments integrity is valid.
        It is the responsibility of the caller to ensure that the deployments are valid.

        :param contract_name: The contract name
        :type contract_name: str | None
        :param chain_id: The chain ID
        :type chain_id: int | str | None
        :param limit: The limit
        :type limit: int | None
        :param config_or_db_path: The config or db path
        :type config_or_db_path: Union[Config, Path, str, None]
        :return: The deployments
        :rtype: list[Deployment]
        """
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
        """Get deployments from the database without an initialized config.

        This method does check if the deployments integrity is valid. If not, it won't be returned.

        :param contract_name: The contract name
        :type contract_name: str | None
        :param chain_id: The chain ID
        :type chain_id: int | str | None
        :param limit: The limit
        :type limit: int | None
        :param config_or_db_path: The config or db path
        :type config_or_db_path: Union[Config, Path, str, None]
        :return: The deployments
        :rtype: list[Deployment]
        """
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
        """Check if the deployment has a matching integrity with the config and contract name.

        :param deployment: The deployment
        :type deployment: Deployment
        :param contract_name: The contract name
        :type contract_name: str | None
        :param config: The config
        :type config: Union[Config, None]
        :return: True if the deployment has a matching integrity, False otherwise
        :rtype: bool
        """
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
        """Returns the Vyper deployer for the contract name.

        :param config: The config
        :type config: Config
        :param contract_name: The contract name
        :type contract_name: str
        :return: The corresponding Vyper deployer
        :rtype: VyperDeployer | ZksyncDeployer
        """
        contract_path = config.find_contract(contract_name)
        return boa.load_partial(str(contract_path.absolute()))

    def get_latest_deployment_unchecked(
        self, contract_name: str | None = None, chain_id: int | str | None = None
    ) -> Deployment | None:
        """Returns the latest deployment of the contract.

        It does not check if the deployment is valid.

        :param contract_name: The contract name
        :type contract_name: str | None
        :param chain_id: The chain ID
        :type chain_id: int | str | None
        :return: The deployment or nothing
        :rtype: Deployment | None
        """
        deployments = self.get_deployments_unchecked(
            contract_name=contract_name, chain_id=chain_id, limit=1
        )
        if len(deployments) > 0:
            return deployments[0]
        return None

    def get_latest_contract_unchecked(
        self, contract_name: str | None = None, chain_id: int | str | None = None
    ) -> ABIContract | None:
        """Returns the latest contract of the contract.

        It does not check if the deployment is valid.

        :param contract_name: The contract name
        :type contract_name: str | None
        :param chain_id: The chain ID
        :type chain_id: int | str | None
        :return: The contract or nothing
        :rtype: ABIContract | None
        """
        deployment = self.get_latest_deployment_unchecked(
            contract_name=contract_name, chain_id=chain_id
        )
        if deployment is not None:
            return self.convert_deployment_to_contract(deployment)
        return None

    def get_latest_deployment_checked(
        self, contract_name: str | None = None, chain_id: int | str | None = None
    ) -> Deployment | None:
        """Returns the latest deployment of the contract.

        It does check if the deployment is valid.

        :param contract_name: The contract name
        :type contract_name: str | None
        :param chain_id: The chain ID
        :type chain_id: int | str | None
        :return: The deployment or nothing
        :rtype: Deployment | None
        """
        deployments = self.get_deployments_checked(
            contract_name=contract_name, chain_id=chain_id, limit=1
        )
        if len(deployments) > 0:
            return deployments[0]
        return None

    def get_latest_contract_checked(
        self, contract_name: str | None = None, chain_id: int | str | None = None
    ) -> ABIContract | None:
        """Returns the latest contract of the contract.

        It does check if the deployment is valid.

        :param contract_name: The contract name
        :type contract_name: str | None
        :param chain_id: The chain ID
        :type chain_id: int | str | None
        :return: The contract or nothing
        :rtype: ABIContract | None
        """
        deployment = self.get_latest_deployment_checked(
            contract_name=contract_name, chain_id=chain_id
        )
        if deployment is not None:
            return self.convert_deployment_to_contract(deployment)
        return None

    def manifest_contract(
        self,
        contract_name: str,
        force_deploy: bool = False,
        address: str | None = None,
        checked: bool = False,
    ) -> VyperContract | ZksyncContract | ABIContract:
        """A wrapper around ``get_or_deploy_named`` that is more explicit about the contract being deployed.

        :param contract_name: The contract name
        :type contract_name: str
        :param force_deploy: If True, will deploy the contract even if the contract has an address in the config file.
        :type force_deploy: bool
        :param address: The address of the contract
        :type address: str | None
        :param checked: If True, will check if the deployment is valid
        :type checked: bool
        :return: The contract
        :rtype: VyperContract | ZksyncContract | ABIContract
        """
        logger.warning(
            "manifest_contract is deprecated and will be removed in a future version. Please use manifest_named."
        )
        return self.get_or_deploy_named(
            contract_name=contract_name, force_deploy=force_deploy, address=address
        )

    def instantiate_contract(
        self, *args, **kwargs
    ) -> VyperContract | ZksyncContract | ABIContract:
        """An alias for ``get_or_deploy_named``.

        Deprecated and will be removed in a future version, please use ``get_or_deploy_named``.
        """
        logger.warning(
            "instantiate_contract is deprecated and will be removed in a future version. Please use manifest_named."
        )
        return self.get_or_deploy_named(*args, **kwargs)

    def get_or_deploy_contract(
        self, *args, **kwargs
    ) -> VyperContract | ZksyncContract | ABIContract:
        """A wrapper around ``get_or_deploy_named``.

        Deprecated and will be removed in a future version, please use ``get_or_deploy_named``.
        """
        logger.warning(
            "get_or_deploy_contract is deprecated and will be removed in a future version. Please use get_or_deploy_named."
        )
        return self.get_or_deploy_named(*args, **kwargs)

    def manifest_named_contract(
        self, *args, **kwargs
    ) -> VyperContract | ZksyncContract | ABIContract:
        """A wrapper around get_or_deploy_named that is more explicit about the contract being deployed."""
        return self.get_or_deploy_named(*args, **kwargs)

    def get_or_deploy_named_contract(
        self, *args, **kwargs
    ) -> VyperContract | ZksyncContract | ABIContract:
        """A wrapper around get_or_deploy_named that is more explicit about the contract being deployed.

        Deprecated and will be removed in a future version, please use ``get_or_deploy_named``.
        """
        logger.warning(
            "get_or_deploy_named_contract is deprecated and will be removed in a future version. Please use get_or_deploy_named."
        )
        return self.get_or_deploy_named(*args, **kwargs)

    def manifest_named(
        self, *args, **kwargs
    ) -> VyperContract | ZksyncContract | ABIContract:
        """A wrapper around get_or_deploy_named that is more explicit about the contract being deployed."""
        return self.get_or_deploy_named(*args, **kwargs)

    def get_or_deploy_named(
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
    ) -> VyperContract | ZksyncContract | ABIContract:
        """Returns or deploys a VyperContract, ZksyncContract, or ABIContract based on the name and address in the config file, or passed to this function.

        The following arguments are mutually exclusive:
            - abi
            - abi_from_explorer

        :param contract_name: the contract name.
        :type contract_name: str
        :param force_deploy: if True, will deploy the contract even if the contract has an address in the config file.
        :type force_deploy: bool
        :param abi: the ABI of the contract. Can be a list, string path to file, string of the ABI, VyperDeployer, VyperContract, ZksyncDeployer, ZksyncContract, ABIContractFactory, or ABIContract.
        :type abi: str | Path | list | VyperDeployer | VyperContract | ZksyncDeployer | ZksyncContract | ABIContractFactory | ABIContract | None
        :param abi_from_explorer: if True, will fetch the ABI from the explorer.
        :type abi_from_explorer: bool | None
        :param deployer_script: If no address is given, this is the path to deploy the contract.
        :type deployer_script: str | Path | None
        :param address: If no address is given, this is the address to deploy the contract.
        :type address: str | None
        :return: The deployed contract instance, or a blank contract if the contract is not found.
        :rtype: VyperContract | ZksyncContract | ABIContract
        """
        # 0. Get args from config & input
        # The NamedContract is a dataclass meant to hold data from the config
        named_contract: NamedContract = self.named_contracts.get(
            contract_name, NamedContract(contract_name)
        )

        if abi_from_explorer and abi:
            raise ValueError(
                "abi and abi_from_explorer are mutually exclusive. Please only provide one."
            )
        abi_or_deployer = abi

        # 0. Setup parameters based on defaults and the inputs to this func
        if not abi_or_deployer and not abi_from_explorer:
            abi_or_deployer = named_contract.get("abi", None)
            vyper_deployer = named_contract.get("vyper_deployer", None)
            if vyper_deployer is not None and abi_or_deployer is None:
                abi_or_deployer = vyper_deployer
        if not abi_from_explorer and not abi_or_deployer:
            abi_from_explorer = named_contract.get("abi_from_explorer", None)
        if not force_deploy:
            force_deploy = named_contract.get("force_deploy", False)
        if not deployer_script:
            deployer_script = named_contract.get("deployer_script", None)
        if not address:
            address = named_contract.get("address", None)

        if not force_deploy:
            # 1. Check DB / Boa contracts
            if address is None:
                if not self.is_local_or_forked_network():
                    vyper_contract: (
                        ABIContract | VyperContract | ZksyncContract | None
                    ) = None
                    # REVIEW: This is a bit confusing.
                    # Right now, if the contract is in the DB, that takes precedence over
                    # a recently deployed contract. This is because the DB is the source of truth.
                    vyper_contract = self.get_latest_contract_unchecked(
                        contract_name=contract_name, chain_id=self.chain_id
                    )
                    if vyper_contract is None:
                        if self._check_valid_deploy(named_contract):
                            vyper_contract = named_contract.recently_deployed_contract
                    if vyper_contract is not None:
                        return vyper_contract
                else:
                    if self._check_valid_deploy(named_contract):
                        return named_contract.recently_deployed_contract
                    else:
                        self.named_contracts[named_contract.contract_name].reset()

            # 2. Assign ABI if address, to see if we need to assign
            else:
                (abi, deployer) = self._get_abi_and_deployer_from_params(
                    named_contract.contract_name,
                    abi_or_deployer,
                    abi_from_explorer,
                    address,
                )
                abi = abi if abi else named_contract.abi
                deployer = deployer if deployer else named_contract.deployer

                if abi:
                    if deployer:
                        return deployer.at(address)
                    else:
                        # Note, we are not putting this into the self.named_contract dict, but maybe we should
                        return ABIContractFactory(named_contract.contract_name, abi).at(
                            address
                        )
                else:
                    logger.info(
                        f"No abi_source or abi_path found for {named_contract.contract_name}, returning a blank contract at {address}"
                    )
                    # We could probably put this into _deploy_named_contract with a conditional
                    blank_contract: VyperDeployer | ZksyncDeployer = boa.loads_partial(
                        ""
                    )
                    vyper_contract = blank_contract.at(address)
                    return vyper_contract

        if deployer_script is None:
            raise ValueError(
                f"Contract {named_contract.contract_name} must be deployed but no deployer_script specified in their {CONFIG_NAME}."
            )
        return self._deploy_named_contract(named_contract, deployer_script)

    def is_local_or_forked_network(self) -> bool:
        """Checks if the network is:

        1. pyevm
        2. eravm
        3. A fork

        :return: True if the network is local or forked, False otherwise.
        :rtype: bool
        """
        return self._is_local_or_forked_network(self.name, self.is_fork)

    def has_explorer(self) -> bool:
        """Check if explorer is set in network config.

        :return: True if explorer is set, False otherwise
        :rtype: bool
        """
        return self.explorer_uri is not None

    def _deploy_named_contract(
        self, named_contract: NamedContract, deployer_script: str | Path
    ) -> VyperContract | ZksyncContract:
        """
        Deploys a named contract from the config and deploys it from the deployer script.

        :param named_contract: the named contract.
        :type named_contract: NamedContract
        :param deployer_script: the path to the deployer script.
        :type deployer_script: str | Path
        :return: the deployed contract.
        :rtype: VyperContract | ZksyncContract
        """
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

    def _add_named_to_db(self, named_contract: NamedContract) -> bool:
        """
        Adds a named contract to the database.

        :param named_contract: the named contract.
        :type named_contract: NamedContract
        :return: True if the contract was added, False otherwise.
        :rtype: bool
        """
        db = get_deployments_db()
        field_names = db._get_fieldnames_str()
        sql = "SELECT {} FROM deployments WHERE json_extract(tx_dict, '$.chainId') = ? AND contract_address = ? ORDER BY broadcast_ts DESC LIMIT 1".format(
            field_names
        )
        cursor = db.db.cursor()
        cursor.execute(
            sql,
            (
                to_hex(self.chain_id),
                named_contract.recently_deployed_contract.address,  # type: ignore
            ),
        )
        contract = cursor.fetchone()
        if contract:
            deployment_id = contract[11]  # This is the deployment ID
            cursor.execute(
                "UPDATE deployments SET contract_name = ? WHERE deployment_id = ?",
                (named_contract.contract_name, deployment_id),
            )
            db.db.commit()
        cursor.close()
        return True if contract else False

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
        """
        Returns the ABI and deployer from the input parameters.

        :param logging_contract_name: the name of the contract.
        :type logging_contract_name: str
        :param abi: the ABI of the contract.
        :type abi: str | Path | list | VyperDeployer | VyperContract | ZksyncContract | ZksyncDeployer | ABIContractFactory | ABIContract | None
        :param abi_from_explorer: whether to get the ABI from explorer.
        :type abi_from_explorer: bool | None
        :param address: the address of the contract.
        :type address: str | None
        :return: the ABI and deployer of the contract.
        :rtype: Tuple[Union[list, None], Union[VyperDeployer, ZksyncDeployer, None]]
        """
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

            abi = boa_get_abi_from_explorer(
                str(address), network_name_or_id=self.alias, quiet=True
            )
        return abi, deployer  # type: ignore

    def get_named_contract(self, contract_name: str) -> NamedContract | None:
        """Returns the named contract with the given name.

        :param contract_name: the name of the contract.
        :type contract_name: str
        :return: the named contract.
        :rtype: NamedContract | None
        """
        return self.named_contracts.get(contract_name, None)

    def get_named_contracts(self) -> dict:
        """Returns a dictionary of named contracts.

        :return: a dictionary of named contracts.
        :rtype: dict
        """
        return self.named_contracts

    def set_boa_eoa(self, account: MoccasinAccount):
        """Sets the boa.env.eoa to the given Moccasin account.

        :param account: the account to set the ``boa.env.eoa`` to.
        :type account: MoccasinAccount
        """
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
    def convert_deployment_to_contract(deployment: Deployment) -> ABIContract:
        """
        Returns the ABIContract from the given deployment.

        :param deployment: the deployment to convert
        :type deployment: Deployment
        :return: the ABIContract at the given address
        :rtype: ABIContract
        """
        contract_factory = ABIContractFactory(
            deployment.contract_name,
            deployment.abi,
            deployment.contract_name + "_" + deployment.source_code["integrity"],
        )
        return contract_factory.at(deployment.contract_address)

    @staticmethod
    def _is_local_or_forked_network(name: str, fork: bool = False) -> bool:
        """
        Returns True if the network is local or forked.

        :param name: the name of the network
        :type name: str
        :param fork: whether to consider forked networks
        :type fork: bool
        :return: True if the network is local or forked, False otherwise
        :rtype: bool
        """
        return name in [PYEVM, ERAVM] or fork

    @staticmethod
    def _check_valid_deploy(named_contract: NamedContract):
        """
        Returns True if the deployed contract is valid, i.e. the contract is actually the same one that boa.env has.

        :param named_contract: the contract to check
        :type named_contract: NamedContract
        :return: True if the contract is valid, False otherwise
        :rtype: bool
        """
        # black magic! check if the contract we have is actually the
        # same one that boa.env has. it could be invalidated in the case
        # of e.g. rollbacks
        deploy = named_contract.recently_deployed_contract
        if deploy is None:
            return False
        boa_contract = boa.env.lookup_contract(deploy.address)
        if boa_contract is not deploy:
            return False
        boa_code = boa.env.get_code(boa_contract.address)
        if boa_code != boa_contract.bytecode and boa_code != deploy.bytecode:
            return False
        return True


class _Networks:
    """A container class that manages network configurations defined in the ``moccasin.toml`` file.

    This class parses and validates network-related settings from the configuration file,
    handling both default network settings and network-specific overrides. It manages
    contract deployments, network connections, and explorer configurations for each network.

    :param toml_data: The configuration data from the ``moccasin.toml`` file
    :type toml_data: dict
    :param project_root: The root directory of the project
    :type project_root: Path

    :ivar _networks: Dictionary mapping network names to their Network objects
    :vartype _networks: dict[str, Network]
    :ivar _default_named_contracts: Default contract configurations that apply across all networks
    :vartype _default_named_contracts: dict[str, NamedContract]
    :ivar _overriden_active_network: Currently active network if manually overridden
    :vartype _overriden_active_network: Network | None
    :ivar default_db_path: Default path for the database storage
    :vartype default_db_path: Path
    :ivar default_network_name: Name of the default network to use
    :vartype default_network_name: str
    """

    _networks: dict[str, Network]
    _default_named_contracts: dict[str, NamedContract]
    _overriden_active_network: Network | None
    default_db_path: Path
    default_network_name: str

    def __init__(self, toml_data: dict, project_root: Path):
        """Initialize the _Networks class."""
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
                    block_identifier=network_data.get("block_identifier", "safe"),
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
        """Return the number of networks.

        :return: The number of networks
        :rtype: int
        """
        return len(self._networks)

    def get_networks(self) -> dict[str, Network]:
        """Return the networks.

        :return: The networks
        :rtype: dict[str, Network]
        """
        return self._networks

    def _generate_network_contracts_from_defaults(
        self, starting_default_contracts: dict, starting_network_contracts_dict: dict
    ) -> dict:
        """Merge default contracts with network-specific contract overrides.

        This method creates a new dictionary of contracts by:

        1. Creating NamedContract instances for network-specific contracts
        2. Applying default contract settings if a default contract exists
        3. Overriding or adding these contracts to the default contracts dictionary

        :param starting_default_contracts: Initial dictionary of default contracts
        :type starting_default_contracts: dict
        :param starting_network_contracts_dict: Dictionary of network-specific contract overrides
        :type starting_network_contracts_dict: dict
        :return: Updated dictionary of contracts with network-specific overrides
        :rtype: dict
        """
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
        """Return the active network.

        :return: The active network
        :rtype: Network
        """
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
        """Return the default database path.

        :return: The default database path
        :rtype: Path
        """
        return self.default_db_path

    def get_network(self, network_name_or_id: str | int) -> Network:
        """Return a network by name or chain ID.

        :param network_name_or_id: The name or chain ID of the network
        :type network_name_or_id: str | int
        :return: The network
        :rtype: Network
        """
        if isinstance(network_name_or_id, int):
            return self.get_network_by_chain_id(network_name_or_id)
        else:
            if network_name_or_id.isdigit():
                return self.get_network_by_chain_id(int(network_name_or_id))
        return self.get_network_by_name(network_name_or_id)

    def get_network_by_chain_id(self, chain_id: int) -> Network:
        """Return a network by chain ID.

        :param chain_id: The chain ID of the network
        :type chain_id: int
        :return: The network
        :rtype: Network
        """
        for network in self._networks.values():
            if network.chain_id == chain_id:
                return network
        raise ValueError(f"Network with chain_id {chain_id} not found.")

    def get_network_by_name(self, alias: str) -> Network:
        """Return a network by name.

        :param alias: The name of the network
        :type alias: str
        :return: The network
        :rtype: Network
        """
        network = self._networks.get(alias, None)
        if not network:
            raise ValueError(f"Network {alias} not found.")
        return network

    def get_or_deploy_named_contract(
        self, *args, **kwargs
    ) -> VyperContract | ZksyncContract | ABIContract:
        """Return a contract by name or deploy it if it's not found.

        :param args: The arguments to pass to the get_or_deploy_named_contract method
        :type args: tuple
        :param kwargs: The keyword arguments to pass to the get_or_deploy_named_contract method
        :type kwargs: dict
        :return: The contract
        :rtype: VyperContract | ZksyncContract | ABIContract
        """
        return self.get_active_network().get_or_deploy_named_contract(*args, **kwargs)

    def set_active_network(
        self, name_of_network_or_network: str | Network, activate_boa=True, **kwargs
    ) -> Network:
        """Set the active network.

        :param name_of_network_or_network: The name or network object of the network
        :type name_of_network_or_network: str | Network
        :param activate_boa: Whether to activate boa on the network
        :type activate_boa: bool
        :param kwargs: The keyword arguments for the Network constructor
        :type kwargs: dict
        :return: The network
        :rtype: Network
        """
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
        """Activate boa on the active network by creating and setting the boa env."""
        active_network = self.get_active_network()
        active_network.create_and_set_or_set_boa_env()
        self._overriden_active_network = None

    @staticmethod
    def _validate_network_contracts_dict(
        contracts: Any, network_name: str | None = None
    ):
        """Validate the structure of network contracts dictionary.

        This method performs two key validations:

        1. Ensures that the contracts parameter is a dictionary
        2. Verifies that each contract entry is also a dictionary

        :param contracts: The contracts dictionary to validate
        :type contracts: Any
        :param network_name: Optional name of the network for more specific error messaging
        :type network_name: str | None, optional
        :raises ValueError: If contracts is not a dictionary or contains non-dictionary entries
        """
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
        """Check and init local network defaults if not already present by adding them to the toml data.

        :param toml_data: The toml data to add defaults to
        :type toml_data: dict
        :return: The toml data with defaults added
        :rtype: dict
        """
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
        """Add fork network defaults options to the network data.

        :param network_data: The fork network data to add defaults to
        :type network_data: dict
        :return: The fork network data with defaults added
        :rtype: dict
        """
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
        """Validate the fork network data.

        :param network_data: The fork network data to validate
        :type network_data: dict
        :raises ValueError: If the fork network data is invalid
        """
        if network_data.get(SAVE_TO_DB, False) is True:
            raise ValueError(
                "You cannot save forked network data to a live database. Please set 'save_to_db' to 'False' or leave it unset."
            )

    @staticmethod
    def _validate_local_network_data(network_data: dict, network_name: str):
        """Validate configuration for local network types.

        Performs multiple validation checks on local network configurations:

        1. Prevents setting restricted keys for local networks
        2. Enforces specific ``is_zksync`` settings for PYEVM and ERAVM networks
        3. Ensures predefined configuration constraints are met

        :param network_data: Configuration dictionary for the local network
        :type network_data: dict
        :param network_name: Name of the local network being validated
        :type network_name: str
        :raises ValueError: If any network configuration violates the validation rules
        """
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


class Config:
    """A wrapper around the ``moccasin.toml`` file, serving as the main entry point for
    performing almost any action with Moccasin.

    This class reads the `moccasin.toml` file and sets up project configuration.

    :param root_path: The root directory of the project. Defaults to None.
    :type root_path: Path, optional

    :ivar _project_root: The root directory of the project.
    :vartype _project_root: Path
    :ivar _toml_data: The parsed TOML data from the `moccasin.toml` file.
    :vartype _toml_data: dict
    :ivar dependencies: A list of dependencies specified in the `moccasin.toml` file.
    :vartype dependencies: list[str]
    :ivar project: A dictionary containing project details from the `moccasin.toml` file.
    :vartype project: dict[str, str]
    :ivar extra_data: A dictionary containing extra data from the `moccasin.toml` file.
    :vartype extra_data: dict[str, Any]
    :ivar networks: A dictionary containing network data from the `moccasin.toml` file.
    :vartype networks: _Networks
    """

    _project_root: Path
    _toml_data: dict
    dependencies: list[str]
    project: dict[str, str]
    extra_data: dict[str, Any]
    networks: _Networks

    def __init__(self, root_path: Path | None):
        """Initialize the Config object."""
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
        """Load configuration from moccasin.toml or pyproject.toml files.

        :param config_path: Path to the moccasin.toml file.
        :type config_path: Path
        :param pyproject_path: Path to the pyproject.toml file. Defaults to None.
        :type pyproject_path: Path or None
        """
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
        """Load environment variables from the .env file specified in the configuration."""
        load_dotenv(dotenv_path=self.project_root.joinpath(self.dot_env))

    def reload(self):
        """Reload the configuration by reinitializing the Config object."""
        self.__init__(self.project_root)

    def get_config_path(self) -> Path:
        """Get the path to the moccasin.toml configuration file.

        :return: The path to the moccasin.toml file.
        :rtype: Path
        """
        return self.config_path

    def read_configs_preserve_comments(
        self,
        moccasin_config_path: Path | None = None,
        pyproject_config_path: Path | None = None,
    ) -> tomlkit.TOMLDocument:
        """Read configuration files while preserving comments.

        :param moccasin_config_path: Path to the moccasin.toml file. Defaults to None.
        :type moccasin_config_path: Path or None
        :param pyproject_config_path: Path to the pyproject.toml file. Defaults to None.
        :type pyproject_config_path: Path or None
        :return: Merged configuration as a TOMLDocument.
        :rtype: tomlkit.TOMLDocument
        """
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

        # Get moccasin specific config from pyproject
        pyproject_mox_config = pyproject_config.get("tool", {}).get("moccasin", {})
        if pyproject_mox_config == {}:
            return moccasin_config

        # Merge the two configs
        merged_config = self.merge_configs(moccasin_config, pyproject_mox_config)
        merged_config = cast(tomlkit.TOMLDocument, merged_config)
        return merged_config

    def read_configs(
        self, moccasin_path: Path | None = None, pyproject_path: Path | None = None
    ) -> dict:
        """Read and merge configuration data from moccasin.toml and pyproject.toml.

        :param moccasin_path: Path to the moccasin.toml file. Defaults to None.
        :type moccasin_path: Path or None
        :param pyproject_path: Path to the pyproject.toml file. Defaults to None.
        :type pyproject_path: Path or None
        :return: Merged configuration data.
        :rtype: dict
        """
        moccasin_data = self.read_moccasin_config(moccasin_path)
        pyproject_data = self.read_pyproject_config(pyproject_path)
        return self.merge_configs(moccasin_data, pyproject_data)

    def read_moccasin_config(self, config_path: Path | None = None) -> dict:
        """Read the moccasin.toml configuration file.

        :param config_path: Path to the moccasin.toml file. Defaults to None.
        :type config_path: Path or None
        :return: Configuration data from moccasin.toml.
        :rtype: dict
        """
        if config_path is None:
            config_path = self.config_path
        return self.read_moccasin_toml(config_path)

    def read_pyproject_config(self, pyproject_path: Path | None = None) -> dict:
        """
        Read the pyproject.toml configuration file.

        :param pyproject_path: Path to the pyproject.toml file. Defaults to None.
        :type pyproject_path: Path or None
        :return: Configuration data from pyproject.toml.
        :rtype: dict
        """
        if pyproject_path is None:
            pyproject_path = self.project_root.joinpath("pyproject.toml")
        return self.read_pyproject_toml(pyproject_path)

    def expand_env_vars(self, value):
        """
        Expand environment variables in the given value.

        :param value: The value to process. Can be a string, list, or dictionary.
        :type value: str, list, or dict
        :return: The value with expanded environment variables.
        :rtype: Same as input type
        """
        if isinstance(value, str):
            return os.path.expandvars(value)
        elif isinstance(value, dict):
            return {k: self.expand_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.expand_env_vars(item) for item in value]
        return value

    def get_networks(self) -> dict[str, Network]:
        """
        Get all network configurations.

        :return: A dictionary of network configurations.
        :rtype: dict[str, Network]
        """
        return self.networks.get_networks()

    def get_active_network(self) -> Network:
        """
        Get the currently active network configuration.

        :return: The active network.
        :rtype: Network
        """
        return self.networks.get_active_network()

    def get_default_db_path(self) -> Path:
        """
        Get the default database path for the active network.

        :return: The path to the default database.
        :rtype: Path
        """
        return self.networks.get_default_db_path()

    def get_or_deploy_named_contract(
        self, *args, **kwargs
    ) -> VyperContract | ZksyncContract | ABIContract:
        """
        Retrieve or deploy a named contract.

        :return: The deployed contract.
        :rtype: VyperContract, ZksyncContract, or ABIContract
        """
        return self.get_active_network().get_or_deploy_named_contract(*args, **kwargs)

    def get_dependencies(self) -> list[str]:
        """
        Get the list of project dependencies.

        :return: A list of dependency names.
        :rtype: list[str]
        """
        return self.dependencies

    def write_dependencies(self, dependencies: list):
        """Writes the dependencies to the config file.

        If a moccasin.toml file exists, it will write there, otherwise, it'll write to pyproject.toml.

        This will overwrite the existing dependencies with the new ones. So if you wish to keep old ones,
        read from the dependencies first.

        :param dependencies: A list of dependencies to write.
        :type dependencies: list
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
        """Get the base path for installing dependencies.

        :return: The path for dependency installation.
        :rtype: Path
        """
        project_root = self._project_root
        base_install_path = project_root / self.project.get(
            DEPENDENCIES_FOLDER, DEPENDENCIES_FOLDER
        )
        base_install_path.mkdir(exist_ok=True, parents=True)
        return base_install_path

    def get_root(self) -> Path:
        """Get the project root path.

        :return: The project root directory.
        :rtype: Path
        """
        return self._project_root

    def find_contract(self, contract_or_contract_path: str) -> Path:
        """Find a contract by its name or path.

        :param contract_or_contract_path: The name or path of the contract.
        :type contract_or_contract_path: str
        :return: The path to the contract.
        :rtype: Path
        """
        return self._find_contract(
            self.project_root,
            self.contracts_folder,
            self.lib_folder,
            contract_or_contract_path,
        )

    def set_active_network(
        self, name_url_or_id: str | Network, activate_boa=True, **kwargs
    ) -> Network:
        """Set the active network.

        :param name_url_or_id: The name, URL, or ID of the network.
        :type name_url_or_id: str or Network
        :param activate_boa: Whether to activate Boa. Defaults to True.
        :type activate_boa: bool
        :return: The active network.
        :rtype: Network
        """
        return self.networks.set_active_network(
            name_url_or_id, activate_boa=activate_boa, **kwargs
        )

    def activate_boa(self):
        """Activate the boa env for the active network."""
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
        """Load configuration from the project root.

        :param project_root: The project root directory. Defaults to None.
        :type project_root: Path or None
        :return: The Config instance.
        :rtype: Config
        """
        if project_root is None:
            project_root = Config.find_project_root()
        return Config(project_root)

    @staticmethod
    def find_project_root(start_path: Path | str | None = None) -> Path:
        """Find the root directory of the project.

        :param start_path: The starting path to search from. Defaults to None.
        :type start_path: Path, str, or None
        :return: The project root directory.
        :rtype: Path
        """
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
        """Read the moccasin.toml configuration file.

        :param config_path: Path to the moccasin.toml file.
        :type config_path: Path
        :return: Configuration data from the file.
        :rtype: dict
        """
        if not config_path.exists():
            return {}
        with open(config_path, "rb") as f:
            return tomllib.load(f)

    @staticmethod
    def read_moccasin_toml_preserve_comments(config_path: Path) -> tomlkit.TOMLDocument:
        """Reads the `moccasin.toml` file at the given path, preserving TOMLDocument comments.

        :param config_path: The path to the configuration file.
        :type config_path: Path
        :return: The TOML document with preserved comments, or an empty document if the file does not exist.
        :rtype: tomlkit.TOMLDocument
        """
        config_path = Config._validated_moccasin_config_path(config_path)
        if not config_path.exists():
            return tomlkit.TOMLDocument()
        with open(config_path, "rb") as f:
            return tomlkit.load(f)

    @staticmethod
    def read_pyproject_toml_preserve_comments(
        config_path: Path,
    ) -> tomlkit.TOMLDocument:
        """Reads the `pyproject.toml` file at the given path, preserving TOMLDocument comments.

        :param config_path: The path to the configuration file.
        :type config_path: Path
        :return: The TOML document with preserved comments, or an empty document if the file does not exist.
        :rtype: tomlkit.TOMLDocument
        """
        config_path = Config._validated_pyproject_config_path(config_path)
        if not config_path.exists():
            return tomlkit.TOMLDocument()
        with open(config_path, "rb") as f:
            return tomlkit.load(f)

    @staticmethod
    def read_pyproject_toml(pyproject_path: Path) -> dict:
        """Reads the `pyproject.toml` file and extracts the `moccasin` configuration.

        :param pyproject_path: The path to the `pyproject.toml` file.
        :type pyproject_path: Path
        :return: The `moccasin` configuration dictionary, or an empty dictionary if the config does not exist.
        :rtype: dict
        """
        if not pyproject_path.exists():
            return {}

        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)

        pyproject_config_toml = pyproject_data.get("tool", {}).get("moccasin", {})
        return pyproject_config_toml

    @staticmethod
    def merge_configs(
        moccasin_config_dict: Union[dict, tomlkit.TOMLDocument],
        pyproject_mox_config_dict: Union[dict, tomlkit.TOMLDocument],
    ) -> Union[dict, tomlkit.TOMLDocument]:
        """Merges the `moccasin` and `pyproject` configuration dictionaries.

        If `dependencies` are defined in both files, `moccasin.toml` takes precedence.

        :param moccasin_config_dict: Configuration from `moccasin.toml`.
        :type moccasin_config_dict: Union[dict, tomlkit.TOMLDocument]
        :param pyproject_mox_config_dict: Moccasin configuration from `pyproject.toml`.
        :type pyproject_mox_config_dict: Union[dict, tomlkit.TOMLDocument]
        :return: The merged configuration dictionary.
        :rtype: Union[dict, tomlkit.TOMLDocument]
        """
        merged = moccasin_config_dict.copy()

        if (
            pyproject_mox_config_dict.get("project", {}).get("dependencies", None)
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

        return deep_update(merged, pyproject_mox_config_dict)

    @staticmethod
    def _validated_pyproject_config_path(config_path: Path):
        """Validates the path to `pyproject.toml`, appending the file name if necessary.

        :param config_path: The input configuration path.
        :type config_path: Path
        :return: The validated path to `pyproject.toml`.
        :rtype: Path
        """
        if not str(config_path).endswith("pyproject.toml"):
            config_path = config_path.joinpath("pyproject.toml")
        return config_path

    @staticmethod
    def _validated_moccasin_config_path(config_path: Path):
        """Validates the path to `moccasin.toml`, appending the file name if necessary.

        :param config_path: The input configuration path.
        :type config_path: Path
        :return: The validated path to `moccasin.toml`.
        :rtype: Path
        """
        if not str(config_path).endswith("moccasin.toml"):
            config_path = config_path.joinpath("moccasin.toml")
        return config_path

    @staticmethod
    def nested_tomlkit_update(
        toml_data: tomlkit.TOMLDocument,
        keys: list,
        value: str | int | float | bool | list | dict,
    ) -> tomlkit.TOMLDocument:
        """Updates a nested key-value pair in a TOML document.

        :param toml_data: The TOML document to update.
        :type toml_data: tomlkit.TOMLDocument
        :param keys: A list of keys representing the nested path.
        :type keys: list
        :param value: The value to set.
        :type value: str | int | float | bool | list | dict
        :return: The updated TOML document.
        :rtype: tomlkit.TOMLDocument
        """
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
        """Finds the specified contract file within the project.

        :param project_root: The root directory of the project.
        :type project_root: str | Path
        :param contracts_folder: The folder containing contract files.
        :type contracts_folder: str
        :param lib_folder: The folder containing library contract files.
        :type lib_folder: str
        :param contract_or_contract_path: The name or path of the contract file.
        :type contract_or_contract_path: str
        :return: The path to the contract file.
        :rtype: Path
        :raises FileNotFoundError: If the contract file is not found.
        :raises FileExistsError: If multiple files with the same name are found.
        """
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
