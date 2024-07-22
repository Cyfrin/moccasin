from pathlib import Path
from gaboon.project.project_class import Project
from vyper.compiler.phases import CompilerData
import json
from gaboon.logging import logger

from typing import Any, List

from boa import load_partial
from boa.contracts.vyper.vyper_contract import VyperDeployer


def main(args: List[Any]):
    my_project: Project = Project(args.project_root)
    compile_project(args.project_root, my_project.out, write_data=True)


def compile_project(
    project_path: Path | None = None,
    build_folder: Path | None = None,
    write_data: bool = False,
) -> int:
    if project_path is None:
        project_path = Project.find_project_root()
    my_project: Project = Project(project_path)
    contracts_location = Path(my_project.src)
    contracts_to_compile = list(contracts_location.rglob("*.vy"))
    logger.info(f"Compiling {len(contracts_to_compile)} contracts to {build_folder}...")
    for contract_path in contracts_to_compile:
        compile(contract_path, build_folder=build_folder, write_data=write_data)
    logger.info("Done Compiling!")
    return 0


def compile(
    contract_path: Path | str,
    build_folder: Path | None = None,
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

    # Create the build folder
    if build_folder:
        build_folder = Path(build_folder)
    else:
        if project_path is None:
            project_path = Project.find_project_root(contract_path)
        build_folder = Path(project_path).joinpath(Project(project_path).out)

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
    logger.debug("Done Compiling!")
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
