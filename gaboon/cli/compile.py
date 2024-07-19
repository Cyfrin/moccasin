from pathlib import Path

from boa import load_partial
from boa.contracts.vyper.vyper_contract import VyperDeployer
from docopt import ParsedOptions, docopt

from gaboon.project.project import Project, find_project_home

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
                with open(contract, "rb") as f:
                    compile(f.read())
    return 0


def compile(contract_path: Path) -> VyperDeployer:
    print("Compiling contracts...")
    return load_partial(contract_path)
