from pathlib import Path
from vyper.compiler.phases import CompilerData
import vyper.compiler.output
import json
from gaboon.logging import logger
from gaboon.constants.vars import BUILD_FOLDER, CONTRACTS_FOLDER
from gaboon.config import get_config, initialize_global_config

from boa import load_partial
from boa.contracts.vyper.vyper_contract import VyperDeployer
from argparse import Namespace


def main(_: Namespace) -> int:
    initialize_global_config()
    project_path: Path = get_config().get_root()
    compile_project(project_path, project_path.joinpath(BUILD_FOLDER), write_data=True)
    return 0


def compile_project(
    project_path: Path | None = None,
    build_folder: Path | None = None,
    write_data: bool = False,
):
    if project_path is None:
        project_path = get_config().get_root()

    contracts_location = project_path / CONTRACTS_FOLDER
    contracts_to_compile = list(contracts_location.rglob("*.vy"))

    if not build_folder:
        build_folder = project_path.joinpath(BUILD_FOLDER)

    logger.info(f"Compiling {len(contracts_to_compile)} contracts to {build_folder}...")

    for contract_path in contracts_to_compile:
        compile_(contract_path, build_folder, write_data=write_data)

    logger.info("Done compiling project!")


def compile_(
    contract_path: Path,
    build_folder: Path,
    compiler_args: dict | None = None,
    project_path: Path | None = None,
    write_data: bool = False,
) -> VyperDeployer:
    logger.debug(f"Compiling contract {contract_path}")

    # Getting the compiler Data
    # (note: boa.load_partial has compiler_data caching infrastructure
    deployer: VyperDeployer = load_partial(str(contract_path), compiler_args)
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
