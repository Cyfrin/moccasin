from pathlib import Path
from dataclasses import dataclass
from typing import Any
from moccasin.constants.vars import SCRIPT_FOLDER
from boa.contracts.vyper.vyper_contract import VyperContract


@dataclass
class MoccasinContract:
    contract_name: str
    force_deploy: bool | None = None
    abi: str | None = None
    abi_from_file_path: str | Path | None = None
    abi_from_etherscan: bool = False
    deployer_path: str | Path | None = None
    address: str | None = None

    def set_defaults(self, other: "MoccasinContract"):
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
        deployer_path: str | Path | None = None,
        script_folder: str | None = SCRIPT_FOLDER,
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
        import importlib

        return importlib.import_module(f"{deployer_module_path}").moccasin_main()
