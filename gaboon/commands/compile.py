from pathlib import Path
from vyper.compiler.phases import CompilerData
import json
from gaboon.logging import logger
from gaboon.constants.vars import BUILD_FOLDER, CONTRACTS_FOLDER
from gaboon.config import get_config, initialize_global_config


from typing import Any, List

from boa import load_partial
from boa.contracts.vyper.vyper_contract import VyperDeployer
from argparse import Namespace


def main(args: Namespace) -> int:
    initialize_global_config()
    project_path: Path = get_config().get_root()
    compile_project(project_path, project_path.joinpath(BUILD_FOLDER), write_data=True)
    return 0


def compile_project(
    project_path: Path | None = None,
    build_folder: Path | None = None,
    write_data: bool = False,
) -> int:
    if project_path is None:
        project_path = get_config().get_root()
    contracts_location = project_path.joinpath(CONTRACTS_FOLDER)
    contracts_to_compile = list(contracts_location.rglob("*.vy"))
    if not build_folder:
        build_folder = project_path.joinpath(BUILD_FOLDER)
    logger.info(f"Compiling {len(contracts_to_compile)} contracts to {build_folder}...")
    for contract_path in contracts_to_compile:
        compile(contract_path, build_folder, write_data=write_data)
    logger.info("Done compiling project!")
    return 0


def compile(
    contract_path: Path,
    build_folder: Path,
    compiler_args: dict | None = None,
    project_path: Path | None = None,
    write_data: bool = False,
) -> VyperDeployer:
    logger.debug(f"Compiling contract {contract_path}")
    # Getting the compiler Data
    deployer: VyperDeployer = load_partial(str(contract_path), compiler_args)
    compiler_data: CompilerData = deployer.compiler_data
    bytecode = compiler_data.bytecode
    abi = generate_abi(compiler_data)

    # Save Compilation Data
    contract_name = Path(contract_path).stem
    build_data = {
        "contract_name": contract_name,
        "bytecode": bytecode.hex(),
        "abi": abi,
    }

    build_file = build_folder / f"{contract_name}.json"
    if write_data:
        build_folder.mkdir(exist_ok=True)
        with open(build_file, "w") as f:
            json.dump(build_data, f, indent=4)
        logger.debug(f"Compilation data saved to {build_file}")
    logger.debug("Done compiling {contract_name}")
    return deployer


def generate_abi(compiler_data: CompilerData) -> list:
    function_signatures = compiler_data.function_signatures
    return [
        {
            "name": func_name,
            "inputs": [
                {"name": inp.name, "type": str(inp.typ)} for inp in func_type.arguments
            ],
            "outputs": [{"name": "", "type": str(func_type.return_type)}]
            if func_type.return_type
            else [],
            "type": "function",
        }
        for func_name, func_type in function_signatures.items()
    ]
