import os
import subprocess
import sys
from argparse import Namespace

from moccasin._sys_path_and_config_setup import _patch_sys_path, get_sys_paths_list
from moccasin.commands.install import mox_install
from moccasin.config import initialize_global_config
from moccasin.logging import logger


def main(args: Namespace) -> int:
    config = initialize_global_config()

    if not args.no_install:
        mox_install(config=config, quiet=True, override_logger=True)

    vyper_args = []
    i = 2  # Start after "mox vyper"

    # Skip --no-install flag
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--no-install":
            i += 1
            continue
        vyper_args.append(arg)
        i += 1

    if not vyper_args:
        logger.error("No arguments provided to pass to the Vyper compiler.")
        logger.info("Example usage: mox vyper -f external_interface src/MyContract.vy")
        return 1

    cmd = ["vyper"] + vyper_args

    logger.debug(f"Running Vyper command: {' '.join(cmd)}")

    # Run the command with patched sys.path for dependency resolution
    with _patch_sys_path(get_sys_paths_list(config)):
        env = os.environ.copy()

        try:
            result = subprocess.run(cmd, check=False, env=env)
            return result.returncode
        except FileNotFoundError:
            logger.error(
                "Vyper compiler not found. Install it with: uv tool install vyper"
            )
            return 1
        except Exception as e:
            logger.error(f"Error running Vyper command: {e}")
            return 1
