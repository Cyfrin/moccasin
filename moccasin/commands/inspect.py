import pprint
from argparse import Namespace
from typing import Any

from moccasin.commands.compile import compile_
from moccasin.config import Config, get_config, initialize_global_config

FUNCTION_SIGNATURES_ALTS = [
    "methods",
    "signatures",
    "selectors",
    "function-selectors",
    "function_signatures",
]


def main(args: Namespace) -> int:
    inspect_type = args.inspect_type.replace("-", "_")
    config = initialize_global_config()
    inspect_contract(args.contract, inspect_type, config=config, print_out=True)
    return 0


def inspect_contract(
    contract: str,
    inspect_type: str,
    config: Config | None = None,
    print_out: bool = False,
) -> Any:
    if config is None:
        config = get_config()

    contract_path = config.find_contract(contract)
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
