from argparse import Namespace
from pathlib import Path
from typing import Any

from moccasin.config import get_config, Config
from moccasin.commands.compile import compile_
import pprint

FUNCTION_SIGNATURES_ALTS = [
    "methods",
    "signatures",
    "selectors",
    "function-selectors",
    "function_signatures",
]


def main(args: Namespace) -> int:
    inspect_type = args.inspect_type.replace("-", "_")
    inspect_contract(args.contract, inspect_type, print_out=True)
    return 0


def inspect_contract(contract: str, inspect_type: str, print_out: bool = False) -> Any:
    config = get_config()

    contract_path = _find_contract(contract, config)
    vyper_deployer = compile_(
        contract_path, config.get_root().joinpath(config.build_folder)
    )

    if inspect_type in FUNCTION_SIGNATURES_ALTS:
        inspect_type = "function_signatures"

    if vyper_deployer is None:
        raise FileNotFoundError(
            f"Could not compile contract '{contract_path}'. Please check the contract file."
        )
    inspected_data = getattr(vyper_deployer.compiler_data, inspect_type)
    final_data = inspected_data

    if inspect_type == "function_signatures":
        final_data = {}
        for _, contract_function in inspected_data.items():
            for signature in contract_function.method_ids:
                int_selector = contract_function.method_ids[signature]
                final_data[signature] = f"{hex(int_selector)} ({int_selector})"

    if print_out:
        print(f"Signatures and selectors for {contract_path.stem}:")
        if inspect_type == "function_signatures":
            for function, selector in final_data.items():
                pprint.pprint(f"{function}: {selector}")
        else:
            pprint.pprint(final_data)
    return final_data


def _find_contract(contract_or_contract_path: str, config: Config) -> Path:
    config_root = config.get_root()
    contract_path: Path | None = None
    if contract_or_contract_path.endswith(".vy"):
        contract_path = config_root / contract_or_contract_path
    else:
        contract_name = contract_or_contract_path + ".vy"

    if not contract_path:
        contracts_location = config_root / config.contracts_folder
        contract_paths = list(contracts_location.rglob(contract_name))
        if not contract_paths:
            raise FileNotFoundError(
                f"Contract file '{contract_name}' not found under '{config_root}'."
            )
        elif len(contract_paths) > 1:
            found_paths = "\n".join(str(path) for path in contract_paths)
            raise FileExistsError(
                f"Multiple contract files named '{contract_name}' found:\n{found_paths}\n"
                "Please specify the path to the contract file."
            )
        else:
            # Exactly one file found
            contract_path = contract_paths[0]
    return contract_path
