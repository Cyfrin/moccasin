from pathlib import Path
from vyper.compiler.phases import CompilerData
import vyper.compiler.output
import json
from gaboon.logging import logger
from gaboon.constants.vars import BUILD_FOLDER, CONTRACTS_FOLDER, GABOON_GITHUB
from gaboon.config import get_config, initialize_global_config
from vyper.exceptions import VersionException
import traceback
import sys

from boa import load_partial
from boa.contracts.vyper.vyper_contract import VyperDeployer
from boa.contracts.vvm.vvm_contract import VVMDeployer
from argparse import Namespace


def main(_: Namespace) -> int:
    initialize_global_config()
    config = get_config()
    project_path: Path = config.get_root()
    compile_project(project_path, project_path.joinpath(config.out_folder), project_path.joinpath(config.contracts_folder), write_data=True)
    return 0


def compile_project(
    project_path: Path | None = None,
    build_folder: Path | None = None,
    contracts_folder: Path | None = None,
    write_data: bool = False,
):
    if project_path is None:
        project_path = get_config().get_root()
    
    if not build_folder:
        build_folder = project_path.joinpath(BUILD_FOLDER)
    
    if not contracts_folder:
        contracts_folder = project_path.joinpath(CONTRACTS_FOLDER)

    contracts_location = project_path.joinpath(contracts_folder)
    contracts_to_compile = list(contracts_location.rglob("*.vy"))

    logger.info(f"Compiling {len(contracts_to_compile)} contracts to {build_folder}...")

    for contract_path in contracts_to_compile:
        compile_(contract_path, build_folder, write_data=write_data)

    logger.info("Done compiling project!")


def compile_(
    contract_path: Path,
    build_folder: Path,
    compiler_args: dict | None = None,
    write_data: bool = False,
) -> VyperDeployer | None:
    logger.debug(f"Compiling contract {contract_path}")

    # Getting the compiler Data
    # (note: boa.load_partial has compiler_data caching infrastructure
    try:
        deployer: VyperDeployer | VVMDeployer = load_partial(str(contract_path), compiler_args)
    except VersionException:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        formatted_exception = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.info(f"Unable to compile {contract_path.stem}:\n\n{formatted_exception}")
        logger.info(f"Perhaps make an issue on the GitHub repo: {GABOON_GITHUB}")
        logger.info("If this contract is optional, you can ignore this error.")
        return None
        
    abi: list
    bytecode: bytes
    if isinstance(deployer, VVMDeployer):
        abi = deployer.abi
        bytecode = deployer.bytecode
    else:
        compiler_data: CompilerData = deployer.compiler_data
        bytecode = compiler_data.bytecode
        abi = vyper.compiler.output.build_abi_output(compiler_data)

    # Save Compilation Data
    contract_name = Path(contract_path).stem

    build_data = {
        "contract_name": contract_name,
        "bytecode": bytecode.hex(),
        "abi": abi,
    }

    if write_data:
        build_file = build_folder / f"{contract_name}.json"
        build_folder.mkdir(exist_ok=True)
        with open(build_file, "w") as f:
            json.dump(build_data, f, indent=4)
        logger.debug(f"Compilation data saved to {build_file}")

    logger.debug("Done compiling {contract_name}")

    return deployer
