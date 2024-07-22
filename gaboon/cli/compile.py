from pathlib import Path
from gaboon.project.project_class import Project
from vyper.compiler.phases import CompilerData
import json

from typing import Any, List

from boa import load_partial
from boa.contracts.vyper.vyper_contract import VyperDeployer


def main(args: List[Any]) -> int:
    my_project: Project = Project(args.project_path)
    compile_project(args.project_path, my_project.out)


def compile_project(
    project_path: Path | None = None, build_folder: Path | None = None
) -> int:
    if project_path is None:
        project_path = Project.find_project_root()
    my_project: Project = Project(project_path)
    contracts_location = Path(my_project.src)
    contracts_to_compile = list(contracts_location.rglob("*.vy"))
    for contract_path in contracts_to_compile:
        compile(contract_path, build_folder=build_folder)
    return 0


def compile(
    contract_path: Path | str,
    build_folder: Path | None = None,
    compiler_args: dict | None = None,
    project_path: Path | None = None,
    write_data: bool = False,
) -> VyperDeployer:
    print("Compiling contracts...")
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
        build_folder = Path(Project(project_path).out)

    # Save Compilation Data
    contract_name = contract_path.stem
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
        print(f"Compilation data saved to {build_file}")
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
