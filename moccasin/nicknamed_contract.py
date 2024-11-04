from dataclasses import dataclass
from pathlib import Path
from typing import Any

from boa.contracts.vyper.vyper_contract import VyperContract, VyperDeployer
from boa_zksync.contract import ZksyncContract
from boa_zksync.deployer import ZksyncDeployer

from moccasin.logging import logger


@dataclass
class NicknamedContract:
    """
    A class to represent a named contract. These hold only data about NicknamedContracts from the config.
    """

    # From the config
    nickname: str
    force_deploy: bool | None = None
    abi: str | None = None
    abi_from_explorer: bool | None = None
    deployer_script: str | Path | None = None
    address: str | None = None

    # If deployed these will not be None, they are for PyEVM, forked networks, or ERAVM only
    deployer: VyperDeployer | ZksyncDeployer | None = None
    recently_deployed_contract: VyperContract | ZksyncContract | None = None

    def set_defaults(self, other: "NicknamedContract"):
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

    def reset(self):
        self.deployer = None
        self.recently_deployed_contract = None

    def is_active(self):
        if self.recently_deployed_contract is None:
            return False
        boa_contract = boa.env._contracts.get(
            Address(self.recently_deployed_contract.address).canonical_address, None
        )
        boa_code = boa.env.get_code(boa_contract.address)
        if boa_contract is None or boa_code is b"":
            return False
        if boa_contract == self.recently_deployed_contract:
            return True
        return False

    def get(self, key: str, otherwise: Any):
        return getattr(self, key, otherwise)

    def _deploy(
        self, script_folder: str, deployer_script: str | Path | None = None
    ) -> VyperContract | ZksyncContract:
        """
        <<<<<<< HEAD:moccasin/named_contract.py
                This function will not save the named contract to the database with it's name!
        =======
                This function will not save the nicknamed contract to the database with it's nickname!
        >>>>>>> 3edced5 (feat: simplified manifest):moccasin/nicknamed_contract.py
        """
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
                f"Your {deployer_module_path} script for {self.nickname} set in deployer path must return a VyperContract or ZksyncContract object"
            )
        self.recently_deployed_contract = vyper_contract
        self.deployer = vyper_contract.deployer
        return vyper_contract
