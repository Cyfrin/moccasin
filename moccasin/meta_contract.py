from pathlib import Path
from dataclasses import dataclass
from typing import Any
from boa.contracts.vyper.vyper_contract import VyperContract
from moccasin.logging import logger


# TODO: Potentially renamed to `NamedContract`, or `ContractConfig`
# TODO: Maybe this has the same interface as VyperDeployer
@dataclass
class MetaContract:
    contract_name: str
    force_deploy: bool | None = None
    abi: str | None = None
    abi_from_file_path: str | Path | None = None
    abi_from_etherscan: bool | None = None
    deployer_path: str | Path | None = None
    address: str | None = None
    vyper_contract: VyperContract | None = None

    def update_from_deployment(self, deployed_contract: VyperContract):
        self.abi = deployed_contract.abi
        self.address = deployed_contract.address
        self.vyper_contract = deployed_contract

    def set_defaults(self, other: "MetaContract"):
        self.force_deploy = (
            self.force_deploy if self.force_deploy is not None else other.force_deploy
        )
        self.abi = self.abi if self.abi is not None else other.abi
        self.abi_from_file_path = (
            self.abi_from_file_path
            if self.abi_from_file_path is not None
            else other.abi_from_file_path
        )
        self.abi_from_etherscan = (
            self.abi_from_etherscan
            if self.abi_from_etherscan is not None
            else other.abi_from_etherscan
        )
        self.deployer_path = (
            self.deployer_path
            if self.deployer_path is not None
            else other.deployer_path
        )
        self.address = self.address if self.address is not None else other.address

    def get(self, key: str, otherwise: Any):
        return getattr(self, key, otherwise)

    def _deploy(
        self,
        script_folder: str,
        deployer_path: str | Path | None = None,
        update_from_deploy: bool = True,
    ) -> VyperContract:
        if deployer_path:
            deployer_path = str(deployer_path)
            deployer_module_path = (
                deployer_path
                if deployer_path.startswith(script_folder)
                else f"{script_folder}.{deployer_path}"
            )
        deployer_path = self.deployer_path if deployer_path is None else deployer_path

        if not deployer_path:
            raise ValueError("Deployer path not provided")

        deployer_module_path = deployer_module_path.replace("/", ".")
        deployer_module_path = (
            deployer_module_path[:-3]
            if deployer_module_path.strip().endswith(".vy")
            else deployer_module_path
        )
        logger.debug(f"Deploying contract using {deployer_module_path}...")
        import importlib

        vyper_contract: VyperContract = importlib.import_module(
            f"{deployer_module_path}"
        ).moccasin_main()
        if not isinstance(vyper_contract, VyperContract):
            raise ValueError(
                f"Your {deployer_module_path} script for {self.contract_name} set in deployer path must return a VyperContract object"
            )
        if update_from_deploy:
            self.update_from_deployment(vyper_contract)
        return vyper_contract
