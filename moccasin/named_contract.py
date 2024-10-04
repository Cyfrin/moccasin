from dataclasses import dataclass
from pathlib import Path
from typing import Any

from boa.contracts.vyper.vyper_contract import VyperContract, VyperDeployer
from boa_zksync.contract import ZksyncContract

from moccasin.logging import logger


@dataclass
class NamedContract:
    contract_name: str
    force_deploy: bool | None = None
    abi: str | None = None
    abi_from_explorer: bool | None = None
    deployer_script: str | Path | None = None
    address: str | None = None
    vyper_contract: VyperContract | None = None
    vyper_deployer: VyperDeployer | None = None

    def update_from_deployed_contract(self, deployed_contract: VyperContract):
        self.abi = deployed_contract.abi
        self.address = deployed_contract.address
        self.vyper_contract = deployed_contract
        self.vyper_deployer = deployed_contract.deployer

    def set_defaults(self, other: "NamedContract"):
        self.force_deploy = (
            self.force_deploy if self.force_deploy is not None else other.force_deploy
        )
        self.abi = self.abi if self.abi is not None else other.abi
        self.abi_from_explorer = (
            self.abi_from_explorer
            if self.abi_from_explorer is not None
            else other.abi_from_explorer
        )
        self.deployer_script = (
            self.deployer_script
            if self.deployer_script is not None
            else other.deployer_script
        )
        self.address = self.address if self.address is not None else other.address

    def get(self, key: str, otherwise: Any):
        return getattr(self, key, otherwise)

    def _deploy(
        self,
        script_folder: str,
        deployer_script: str | Path | None = None,
        update_from_deploy: bool = True,
    ) -> VyperContract | ZksyncContract:
        if deployer_script:
            deployer_script = str(deployer_script)
            deployer_module_path = (
                deployer_script
                if deployer_script.startswith(script_folder)
                else f"{script_folder}.{deployer_script}"
            )
        deployer_script = (
            self.deployer_script if deployer_script is None else deployer_script
        )

        if not deployer_script:
            raise ValueError("Deployer path not provided")

        deployer_module_path = deployer_module_path.replace("/", ".")
        deployer_module_path = (
            deployer_module_path[:-3]
            if deployer_module_path.strip().endswith(".py")
            else deployer_module_path
        )
        logger.debug(f"Deploying contract using {deployer_module_path}...")
        import importlib

        vyper_contract: VyperContract | ZksyncContract = importlib.import_module(
            f"{deployer_module_path}"
        ).moccasin_main()

        if not isinstance(vyper_contract, VyperContract) and not isinstance(
            vyper_contract, ZksyncContract
        ):
            raise ValueError(
                f"Your {deployer_module_path} script for {self.contract_name} set in deployer path must return a VyperContract or ZksyncContract object"
            )
        if update_from_deploy:
            self.update_from_deployed_contract(vyper_contract)
        return vyper_contract
