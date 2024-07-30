from pathlib import Path
import subprocess
import os

from tests.cli.conftest import COMPLEX_PROJECT_PATH

def test_run_help(gab_path):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [gab_path, "run", "-h"],
            check=True,
            capture_output=True,
            text=True,
        )
        assert "Gaboon CLI run" in result.stdout
    finally:
        os.chdir(current_dir)


