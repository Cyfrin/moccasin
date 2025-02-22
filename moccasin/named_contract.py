from dataclasses import dataclass
from pathlib import Path
from typing import Any

from boa.contracts.vyper.vyper_contract import VyperContract, VyperDeployer
from boa_zksync.contract import ZksyncContract
from boa_zksync.deployer import ZksyncDeployer

from moccasin.logging import logger


@dataclass
class NamedContract:
    """A class to represent a named contract.

    This class holds data about NamedContracts from the configuration and manages their deployment.

    :param contract_name: The name of the contract
    :type contract_name: str
    :param force_deploy: Whether to force deployment of the contract
    :type force_deploy: bool | None
    :param abi: The ABI of the contract
    :type abi: str | None
    :param abi_from_explorer: Whether to fetch the ABI from the explorer
    :type abi_from_explorer: bool | None
    :param deployer_script: The path to the deployer script
    :type deployer_script: str | Path | None
    :param address: The address of the contract
    :type address: str | None
    :param deployer: The deployer instance for the contract
    :type deployer: VyperDeployer | ZksyncDeployer | None
    :param recently_deployed_contract: The recently deployed contract instance
    :type recently_deployed_contract: VyperContract | ZksyncContract | None
    """

    # From the config
    contract_name: str
    force_deploy: bool | None = None
    abi: str | None = None
    abi_from_explorer: bool | None = None
    deployer_script: str | Path | None = None
    address: str | None = None

    # If deployed these will not be None, they are for PyEVM, forked networks, or ERAVM only
    deployer: VyperDeployer | ZksyncDeployer | None = None
    recently_deployed_contract: VyperContract | ZksyncContract | None = None

    def set_defaults(self, other: "NamedContract"):
        """Set default values from another NamedContract instance if they are not already set.

        :param other: Another NamedContract instance to copy defaults from
        :type other: NamedContract
        """
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
        """Reset the deployer and recently deployed contract to None."""
        self.deployer = None
        self.recently_deployed_contract = None

    def get(self, key: str, otherwise: Any):
        """Get a NamedContract attribute value or return a default if the attribute is not set.

        :param key: The attribute name to get
        :type key: str
        :param otherwise: The default value to return if the attribute is not set
        :type otherwise: Any
        :return: The attribute value or the default value
        :rtype: Any
        """
        return getattr(self, key, otherwise)

    def _deploy(
        self, script_folder: str, deployer_script: str | Path | None = None
    ) -> VyperContract | ZksyncContract:
        """Deploy the contract using the specified deployer script.

        This function will not save the named contract to the database with it's name!

        :param script_folder: The folder containing the deployer scripts
        :type script_folder: str
        :param deployer_script: The path to the deployer script, defaults to None
        :type deployer_script: str | Path | None
        :return: The deployed contract instance
        :rtype: VyperContract | ZksyncContract
        :raises ValueError: If deployer path is not provided or invalid contract type is returned
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
                f"Your {deployer_module_path} script for {self.contract_name} set in deployer path must return a VyperContract or ZksyncContract object"
            )
        self.recently_deployed_contract = vyper_contract
        self.deployer = vyper_contract.deployer
        return vyper_contract
