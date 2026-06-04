import shlex
import subprocess
from argparse import Namespace

from moccasin.config import get_or_initialize_config
from moccasin.logging import logger


def main(args: Namespace) -> int:
    """Run a shell command declared under ``[scripts]`` in ``moccasin.toml``.

    Forms:
        mox task                 # list all configured scripts
        mox task --list          # list all configured scripts
        mox task <name>          # run the named script
        mox task <name> -- ...   # forward extra args to the script
    """
    config = get_or_initialize_config()
    scripts: dict[str, str] = config.get_scripts()

    name: str | None = getattr(args, "name", None)
    list_only: bool = bool(getattr(args, "list", False))

    if list_only or name is None:
        _print_scripts(scripts)
        return 0

    if name not in scripts:
        logger.error(f"Unknown script '{name}'.")
        if scripts:
            logger.info(
                "Available scripts: " + ", ".join(sorted(scripts.keys()))
            )
        else:
            logger.info(
                "No [scripts] table found in moccasin.toml."
            )
        return 1

    cmd = scripts[name]
    forward = list(getattr(args, "forward_args", None) or [])
    if forward:
        cmd = cmd + " " + " ".join(shlex.quote(arg) for arg in forward)

    logger.info(f"Running script '{name}': {cmd}")
    result = subprocess.run(cmd, shell=True, check=False)
    return result.returncode


def _print_scripts(scripts: dict[str, str]) -> None:
    if not scripts:
        logger.info("No scripts defined.")
        return
    logger.info("Available scripts:")
    width = max(len(name) for name in scripts)
    for name in sorted(scripts):
        logger.info(f"  {name.ljust(width)}  {scripts[name]}")
