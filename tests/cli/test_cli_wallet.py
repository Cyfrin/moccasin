from pathlib import Path
import os
import subprocess
from tests.conftest import (
    COMPLEX_PROJECT_PATH,
)


def test_run_help(gab_path):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [gab_path, "wallet", "-h"],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Gaboon CLI wallet" in result.stdout
