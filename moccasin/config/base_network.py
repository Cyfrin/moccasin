from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Tuple, Union

import boa
from boa.contracts.abi.abi_contract import ABIContract, ABIContractFactory
from boa.contracts.vyper.vyper_contract import VyperContract, VyperDeployer
from boa.deployments import (
    Deployment,
    DeploymentsDB,
    get_deployments_db,
    set_deployments_db,
)
from boa.environment import Env
from boa.util.abi import Address
from boa_zksync import set_zksync_env, set_zksync_fork, set_zksync_test_env
from boa_zksync.contract import ZksyncContract
from boa_zksync.deployer import ZksyncDeployer
from eth_utils import to_hex

from moccasin.constants.vars import (
    CONFIG_NAME,
    DB_PATH_LOCAL_DEFAULT,
    ERAVM,
    GET_CONTRACT_SQL,
    PYEVM,
    SQL_AND,
    SQL_CHAIN_ID,
    SQL_CONTRACT_NAME,
    SQL_LIMIT,
    SQL_WHERE,
)
from moccasin.logging import logger
from moccasin.moccasin_account import MoccasinAccount
from moccasin.named_contract import NamedContract

if TYPE_CHECKING:
    from boa.network import NetworkEnv
    from boa.verifiers import VerificationResult
    from boa_zksync import ZksyncEnv

_AnyEnv = Union["NetworkEnv", "Env", "ZksyncEnv"]


@dataclass
class BaseNetwork(ABC):
    """
    Base implemention for Network class.
    
    @dev We are using abstraction to allow the Network class
        implementation in Config, since there are dependencies in
        some methods. The goal is to avoid circular imports.
    """

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
    named_contracts: dict[str, NamedContract] = field(default_factory=dict)
    prompt_live: bool = True
    save_to_db: bool = True
    live_or_staging: bool = True
    db_path: str | Path = DB_PATH_LOCAL_DEFAULT
    extra_data: dict[str, Any] = field(default_factory=dict)
    _network_env: _AnyEnv | None = None

    def _set_boa_env(self) -> _AnyEnv:
        """Sets the boa.env to the current network, this additionally sets up the database."""
        # perf: save time on imports in the (common) case where
        # we just import config for its utils but don't actually need
        # to switch networks
        from boa.network import EthereumRPC, NetworkEnv

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

    def is_matching_boa(self) -> bool:
        """Returns True if the current network is the active network in boa.
        This is a good way to test if you've overriden boa as the "active" network.
        """
        return boa.env.nickname == self.name

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

    def set_kwargs(self, **kwargs):
        for key, value in kwargs.items():
            if value is not None:
                setattr(self, key, value)

    def _set_boa_db(self) -> None:
        db: DeploymentsDB
        if self.save_to_db:
            db = DeploymentsDB(path=self.db_path)
        else:
            db = DeploymentsDB(path=DB_PATH_LOCAL_DEFAULT)
        set_deployments_db(db)

    def create_and_set_or_set_boa_env(self, **kwargs) -> _AnyEnv:
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
        if db is None:
            db = get_deployments_db()
        chain_id = to_hex(chain_id) if chain_id is not None else None
        if not isinstance(limit, int) and not isinstance(limit, type(None)):
            raise ValueError(f"Limit must be an integer, not {type(limit)}.")
        final_sql, params = self._generate_sql_from_args(
            contract_name=contract_name, chain_id=chain_id, limit=limit, db=db
        )
        return db._get_deployments_from_sql(final_sql, params)

    @abstractmethod
    def _get_deployments_iterator(
        self,
        contract_name: str | None = None,
        chain_id: int | str | None = None,
        limit: int | None = None,
        *args,
        **kwargs,
    ) -> Iterator[Deployment]:
        raise NotImplementedError

    @abstractmethod
    def get_deployments_unchecked(
        self,
        contract_name: str | None = None,
        limit: int | None = None,
        chain_id: int | str | None = None,
        *args,
        **kwargs,
    ) -> list[Deployment]:
        raise NotImplementedError

    @abstractmethod
    def get_deployments_checked(
        self,
        contract_name: str | None = None,
        limit: int | None = None,
        chain_id: int | str | None = None,
        *args,
        **kwargs,
    ) -> list[Deployment]:
        raise NotImplementedError

    @abstractmethod
    def has_matching_integrity(
        self, deployment: Deployment, contract_name: str | None, *args, **kwargs
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_deployer_from_contract_name(
        self, contract_name: str, *args, **kwargs
    ) -> VyperDeployer | ZksyncDeployer:
        raise NotImplementedError

    def get_latest_deployment_unchecked(
        self, contract_name: str | None = None, chain_id: int | str | None = None
    ) -> Deployment | None:
        deployments = self.get_deployments_unchecked(
            contract_name=contract_name, chain_id=chain_id, limit=1
        )
        if len(deployments) > 0:
            return deployments[0]
        return None

    def get_latest_contract_unchecked(
        self, contract_name: str | None = None, chain_id: int | str | None = None
    ) -> ABIContract | None:
        deployment = self.get_latest_deployment_unchecked(
            contract_name=contract_name, chain_id=chain_id
        )
        if deployment is not None:
            return self.convert_deployment_to_contract(deployment)
        return None

    def get_latest_deployment_checked(
        self, contract_name: str | None = None, chain_id: int | str | None = None
    ) -> Deployment | None:
        deployments = self.get_deployments_checked(
            contract_name=contract_name, chain_id=chain_id, limit=1
        )
        if len(deployments) > 0:
            return deployments[0]
        return None

    def get_latest_contract_checked(
        self, contract_name: str | None = None, chain_id: int | str | None = None
    ) -> ABIContract | None:
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
        """A wrapper around get_or_deploy_named_contract that is more explicit about the contract being deployed."""
        logger.warning(
            "manifest_contract is deprecated and will be removed in a future version. Please use manifest_named."
        )
        return self.get_or_deploy_named(
            contract_name=contract_name, force_deploy=force_deploy, address=address
        )

    def instantiate_contract(
        self, *args, **kwargs
    ) -> VyperContract | ZksyncContract | ABIContract:
        """An alias for get_or_deploy_named_contract."""
        logger.warning(
            "instantiate_contract is deprecated and will be removed in a future version. Please use manifest_named."
        )
        return self.get_or_deploy_named(*args, **kwargs)

    def get_or_deploy_contract(
        self, *args, **kwargs
    ) -> VyperContract | ZksyncContract | ABIContract:
        logger.warning(
            "get_or_deploy_named_contract is deprecated and will be removed in a future version. Please use get_or_deploy_named."
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
        """A wrapper around get_or_deploy_named that is more explicit about the contract being deployed."""
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
        """Returns True if network is:
        1. pyevm
        2. eravm
        3. A fork
        """
        return self._is_local_or_forked_network(self.name, self.is_fork)

    def has_explorer(self) -> bool:
        return self.explorer_uri is not None

    @abstractmethod
    def _deploy_named_contract(
        self, named_contract: NamedContract, deployer_script: str | Path
    ) -> VyperContract | ZksyncContract:
        raise NotImplementedError

    def _add_named_to_db(self, named_contract: NamedContract) -> bool:
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

    @abstractmethod
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
        raise NotImplementedError

    def get_named_contract(self, contract_name: str) -> NamedContract | None:
        return self.named_contracts.get(contract_name, None)

    def get_named_contracts(self) -> dict:
        return self.named_contracts

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
    def convert_deployment_to_contract(deployment: Deployment) -> ABIContract:
        contract_factory = ABIContractFactory(
            deployment.contract_name,
            deployment.abi,
            deployment.contract_name + "_" + deployment.source_code["integrity"],
        )
        return contract_factory.at(deployment.contract_address)

    @staticmethod
    def _is_local_or_forked_network(name: str, fork: bool = False) -> bool:
        return name in [PYEVM, ERAVM] or fork

    @staticmethod
    def _check_valid_deploy(named_contract: NamedContract):
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
