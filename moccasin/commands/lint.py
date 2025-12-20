import os
import subprocess
import sys
from argparse import Namespace

from moccasin._sys_path_and_config_setup import _patch_sys_path, get_sys_paths_list
from moccasin.commands.install import mox_install
from moccasin.config import initialize_global_config
from moccasin.logging import logger


def main(args: Namespace) -> int:
    """Lint Vyper source code using natrix."""
    config = initialize_global_config()

    if not args.no_install:
        mox_install(config=config, quiet=True, override_logger=True)

    lint_args = []
    i = 2  # Start after "mox lint"

    # Skip --no-install flag
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--no-install":
            i += 1
            continue
        lint_args.append(arg)
        i += 1

    # If no files specified in args, add all .vy files from src folder
    files_in_args = [arg for arg in lint_args if not arg.startswith("-")]
    if not files_in_args:
        src_folder = config.project_root / config.src_folder
        if src_folder.exists():
            vy_files = list(src_folder.glob("**/*.vy"))
            if vy_files:
                lint_args.extend([str(f) for f in vy_files])

        if not lint_args:
            logger.error("No Vyper files found to lint.")
            logger.info(
                f"Make sure you have .vy files in your {src_folder} directory or specify files explicitly."
            )
            return 1

    # natrix uses subcommands, so we call "natrix lint" with the args
    cmd = ["natrix", "lint"] + lint_args

    logger.debug(f"Running natrix command: {' '.join(cmd)}")

    # Run the command with patched sys.path for dependency resolution
    with _patch_sys_path(get_sys_paths_list(config)):
        env = os.environ.copy()

        try:
            result = subprocess.run(cmd, check=False, env=env)
            return result.returncode
        except FileNotFoundError:
            logger.error("natrix linter not found")
            logger.error("Install it with: uv tool install natrix")
            return 1
        except Exception as e:
            logger.error(f"Error running natrix command: {e}")
            return 1