from pathlib import Path
from gaboon.project.project import Project, find_project_home
from boa import load_partial
from boa.contracts.vyper.vyper_contract import VyperDeployer
from vyper.compiler.phases import CompilerData
import json

from typing import Any, List, Optional
import json
from vyper.compiler.phases import CompilerData

from boa import load_partial
from boa.contracts.vyper.vyper_contract import VyperDeployer

from gaboon.project.project import Project, find_project_home


def main(_: List[Any]) -> int:
    compile_project()


def compile_project() -> int:
    project_path = find_project_home()
    my_project: Project = Project(project_path)
    contracts_location = Path(my_project.config.src)
    # recursively find all contracts in the contracts directory
    contracts_to_compile = list(contracts_location.rglob("*.vy"))
    for contract_path in contracts_to_compile:
        compile(contract_path)
    return 0


def compile(contract_path: Path, compiler_args: Optional[dict]) -> VyperDeployer:
    print("Compiling contracts...")
    # Getting the compiler Data
    deployer = load_partial(str(contract_path), compiler_args)
    compiler_data: CompilerData = deployer.compiler_data
    bytecode = compiler_data.bytecode
    abi = generate_abi(compiler_data)

    # Create the build folder
    build_folder = Path("build")
    build_folder.mkdir(exist_ok=True)

    # Save Compilation Data
    contract_name = contract_path.stem
    build_data = {
        "contract_name": contract_name,
        "bytecode": bytecode.hex(),  # Convert to HexString
        "abi": abi,
    }

    build_file = build_folder / f"{contract_name}.json"
    with open(build_file, "w") as f:
        json.dump(build_data, f, indent=4)

    print(f"Compilation data saved to {build_file}")


# Generating the ABI based on the Compiler Data.


def generate_abi(compiler_data) -> list:
    abi = []
    for func_name, func_type in compiler_data.function_signatures.items():
        entry = {
            "name": func_name,
            "inputs": [
                {"name": inp.name, "type": str(inp.typ)} for inp in func_type.arguments
            ],
            "outputs": (
                [{"name": "", "type": str(func_type.return_type)}]
                if func_type.return_type
                else []
            ),
            "type": "function",
        }
        abi.append(entry)
    return abi
