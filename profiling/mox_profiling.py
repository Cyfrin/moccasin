import os
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from profiling.constants import MOCK_PROJECT


def parse_args():
    """Parse command line arguments for the mox CLI profiling script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Profile a single mox CLI command in a TemporaryDirectory."
    )
    parser.add_argument(
        "--command",
        type=str,
        required=True,
        help="Command to run (as a single string). No need for mox prefix.",
    )
    return parser.parse_args()


def run_in_tempdir(command: str):
    """Run a command in a temporary directory with profiling enabled.

    :param command: The command to run as a string.
    """
    print(f"[INFO] Running in tempdir (profiled): {command}")
    with TemporaryDirectory() as tmp_dir:
        shutil.copytree(MOCK_PROJECT, Path(tmp_dir), dirs_exist_ok=True)
        current_dir = Path.cwd()
        try:
            os.chdir(tmp_dir)
            # Set MOX_PROFILE=1 for this subprocess
            env = os.environ.copy()
            env["MOX_PROFILE"] = "1"
            argv = command.split()
            # Use subprocess directly to pass env
            cmd = ["mox"] + argv + ["--quiet"]
            subprocess.run(cmd, check=True, text=True, env=env)
        finally:
            os.chdir(current_dir)


def main():
    args = parse_args()
    command = args.command.strip()
    run_in_tempdir(command)


if __name__ == "__main__":
    main()
