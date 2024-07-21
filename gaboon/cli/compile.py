from pathlib import Path
from docopt import docopt
from docopt import ParsedOptions
from gaboon.project.project import Project, find_project_home
from boa import load_partial
from boa.contracts.vyper.vyper_contract import VyperDeployer
from vyper.compiler.phases import CompilerData
import json


__doc__ = """Usage: gab (compile | build) [<contract_name> ...] [options]

You can use `gab compile` or `gab build` interchangeably.

Arguments:
    [<contract_name> ...]    Optional list of contract names to compile.

Options:
  --all -a --force -f   Recompile all contracts
  --help -h             Display this message

Compiles the contracts in the contracts folder, and saves the compliation data to the build folder.
"""


def main() -> int:
    args: ParsedOptions = docopt(__doc__)
    project_path = find_project_home()
    my_project: Project = Project(project_path)
    contracts_location = my_project.config.src
    contracts_to_compile = args["<contract_name>"]
    if len(contracts_to_compile) == 0:
        for contract in Path(contracts_location).rglob("*"):
            if contract.suffix == ".vy":
                compile(contract)

    return 0


def compile(contract_path: Path) -> VyperDeployer:
    print("Compiling contracts...")
    compiler_args = {}
    deployer = load_partial(str(contract_path), compiler_args)

    # Getting the compiler Data

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
