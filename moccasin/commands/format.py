import subprocess
from argparse import Namespace

from moccasin.config import get_config, initialize_global_config
from moccasin.logging import logger


def main(args: Namespace) -> int:
    """Format Vyper source code using mamushi."""
    initialize_global_config()
    config = get_config()

    # Get the format args passed from the CLI
    format_args = getattr(args, "format_args", [])

    # If no files specified in args, add all .vy files from src folder
    files_in_args = [arg for arg in format_args if not arg.startswith("-")]
    if not files_in_args:
        src_folder = config.project_root / config.src_folder
        if src_folder.exists():
            vy_files = list(src_folder.glob("**/*.vy"))
            if vy_files:
                format_args.extend([str(f) for f in vy_files])

        if not format_args:
            logger.error("No Vyper files found to format.")
            logger.info(
                f"Make sure you have .vy files in your {src_folder} directory or specify files explicitly."
            )
            return 1

    cmd = ["mamushi"] + format_args

    logger.debug(f"Running mamushi command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        logger.error("mamushi formatter not found.")
        logger.error("Install it with: uv tool install mamushi")
        return 1
    except Exception as e:
        logger.error(f"Error running mamushi command: {e}")
        return 1
