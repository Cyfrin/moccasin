import json
import multiprocessing
import os
import sys
import time
import traceback
from argparse import Namespace
from pathlib import Path

import vyper.compiler.output
from boa import load_partial
from boa.contracts.vvm.vvm_contract import VVMDeployer
from boa.contracts.vyper.vyper_contract import VyperDeployer
from vyper.compiler.phases import CompilerData
from vyper.exceptions import VersionException, _BaseVyperException

from moccasin._sys_path_and_config_setup import _patch_sys_path, get_sys_paths_list
from moccasin.config import Config, get_config, initialize_global_config
from moccasin.constants.vars import (
    BUILD_FOLDER,
    CONTRACTS_FOLDER,
    ERAVM,
    MOCCASIN_GITHUB,
)
from moccasin.logging import logger


def main(args: Namespace) -> int:
    config = initialize_global_config()
    project_path: Path = config.get_root()

    is_zksync: bool = _set_zksync_test_env_if_applicable(args, config)

    with _patch_sys_path(get_sys_paths_list(config)):
        if args.contract_or_contract_path:
            contract_path = config.find_contract(args.contract_or_contract_path)
            compile_(
                contract_path,
                project_path.joinpath(config.out_folder),
                is_zksync=is_zksync,
                write_data=True,
            )
            logger.info(f"Done compiling {contract_path.stem}")
        else:
            compile_project(
                project_path,
                project_path.joinpath(config.out_folder),
                project_path.joinpath(config.contracts_folder),
                is_zksync=is_zksync,
                write_data=True,
            )
    return 0


def _set_zksync_test_env_if_applicable(args: Namespace, config: Config) -> bool:
    is_zksync = args.is_zksync if args.is_zksync is not None else None

    if is_zksync:
        config.set_active_network(ERAVM)
        return True

    if args.network is not None and is_zksync is None:
        config.set_active_network(args.network)
        is_zksync = config.get_active_network().is_zksync

    if config.default_network is not None and is_zksync is None:
        config.set_active_network(config.default_network)
        is_zksync = config.get_active_network().is_zksync

    if is_zksync is None:
        is_zksync = False

    return is_zksync


def _get_cpu_count():
    if hasattr(os, "process_cpu_count"):
        # python 3.13+
        return os.process_cpu_count()
    return os.cpu_count()


def compile_project(
    project_path: Path | None = None,
    build_folder: Path | None = None,
    contracts_folder: Path | None = None,
    is_zksync: bool = False,
    write_data: bool = False,
):
    if project_path is None:
        project_path = get_config().get_root()

    if not build_folder:
        build_folder = project_path.joinpath(BUILD_FOLDER)

    if not contracts_folder:
        contracts_folder = project_path.joinpath(CONTRACTS_FOLDER)

    contracts_location = project_path.joinpath(contracts_folder)
    contracts_to_compile = list(contracts_location.rglob("*.vy"))

    try:
        build_folder_relpath: str = os.path.relpath(build_folder)
    except ValueError:
        build_folder_relpath = str(build_folder)
    logger.info(
        f"Compiling {len(contracts_to_compile)} contracts to {build_folder_relpath}/..."
    )

    multiprocessing.set_start_method("fork", force=False)

    n_cpus = max(1, _get_cpu_count() - 2)
    jobs = []

    with multiprocessing.Pool(n_cpus) as pool:
        for contract_path in contracts_to_compile:
            res = pool.apply_async(
                compile_,
                (contract_path, build_folder),
                dict(is_zksync=is_zksync, write_data=write_data),
            )
            jobs.append(res)

        # loop over jobs waiting for them to complete.
        # use nowait check so that bubbling up of exceptions isn't blocked
        # by a slow job
        while len(jobs) > 0:
            tmp = []
            for job in jobs:
                if job.ready():
                    # bubble up any exceptions
                    try:
                        job.get()
                    except vyper.exceptions.InitializerException:
                        logger.info(
                            f"Skipping contract {contract_path.stem} due to uninitialized."
                        )
                        continue
                else:
                    tmp.append(job)
            jobs = tmp
            time.sleep(0.001)  # relax

    logger.info("Done compiling project!")


def compile_(
    contract_path: Path,
    build_folder: Path,
    compiler_args: dict | None = None,
    is_zksync: bool = False,
    write_data: bool = False,
) -> VyperDeployer | None:
    logger.debug(f"Compiling contract {contract_path}")

    # Getting the compiler Data
    # (note: boa.load_partial has compiler_data caching infrastructure
    try:
        deployer: VyperDeployer | VVMDeployer = load_partial(
            str(contract_path), compiler_args
        )
    except VersionException:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        formatted_exception = "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
        logger.info(f"Unable to compile {contract_path.stem}:\n\n{formatted_exception}")
        logger.info(f"Perhaps make an issue on the GitHub repo: {MOCCASIN_GITHUB}")
        logger.info("If this contract is optional, you can ignore this error.")
        return None
    except _BaseVyperException as exc:
        if callable(exc._hint):
            exc._hint = exc._hint()
        raise exc

    abi: list
    bytecode: bytes
    vm = "evm"

    if is_zksync:
        abi = deployer._abi
        bytecode = deployer.zkvyper_data.bytecode
        vm = "eravm"
    else:
        if isinstance(deployer, VVMDeployer):
            abi = deployer.abi
            bytecode = deployer.bytecode
        else:
            compiler_data: CompilerData = deployer.compiler_data
            bytecode = compiler_data.bytecode
            abi = vyper.compiler.output.build_abi_output(compiler_data)

    # Save Compilation Data
    contract_name = Path(contract_path).stem
    build_data = {
        "contract_name": contract_name,
        "bytecode": bytecode.hex(),
        "abi": abi,
        "vm": vm,
    }

    if write_data:
        build_file = build_folder / f"{contract_name}.json"
        build_folder.mkdir(exist_ok=True)
        with open(build_file, "w") as f:
            json.dump(build_data, f, indent=4)
        logger.debug(f"Compilation data saved to {build_file}")

    logger.debug(f"Done compiling {contract_name}")

    return deployer
