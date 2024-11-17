import pprint
from argparse import Namespace
from typing import Any

from moccasin._sys_path_and_config_setup import _patch_sys_path, get_sys_paths_list
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

    # We should probably refactor this so that `_patch_sys_path` is auto called on stuff like "compile"
    # I keep forgetting to add it and it screws stuff up
    with _patch_sys_path(get_sys_paths_list(config)):
        contract_path = config.find_contract(contract)
        vyper_deployer = compile_(
            contract_path,
            config.get_root().joinpath(config.out_folder),
            is_zksync=False,
            write_data=False,
        )

    if inspect_type in FUNCTION_SIGNATURES_ALTS:
        inspect_type = "function_signatures"

    if vyper_deployer is None:
        raise FileNotFoundError(
            f"Could not compile contract '{contract_path}'. Please check the contract file."
        )
    initial_inspected_data = getattr(vyper_deployer.compiler_data, inspect_type)
    final_data = initial_inspected_data.copy()

    if inspect_type == "function_signatures":
        final_data = {}
        global_inspected_data = getattr(
            vyper_deployer.compiler_data.global_ctx, "exposed_functions"
        )

        for signature in initial_inspected_data.keys():
            contract_function = initial_inspected_data[signature]
            for signature in contract_function.method_ids:
                int_selector = contract_function.method_ids[signature]
                final_data[signature] = f"{hex(int_selector)} ({int_selector})"

        for contract_function in global_inspected_data:
            for signature in contract_function.method_ids:
                int_selector = contract_function.method_ids[signature]
                final_data[signature] = f"{hex(int_selector)} ({int_selector})"

    if print_out:
        if inspect_type == "function_signatures":
            print(f"Signatures and selectors for {contract_path.stem}:")
            for function, selector in final_data.items():
                pprint.pprint(f"{function}: {selector}")
        else:
            pprint.pprint(final_data)
    return final_data
