import os
import subprocess
from pathlib import Path

from tests.conftest import COMPLEX_PROJECT_PATH


def test_run_help(mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "wallet", "-h"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "Moccasin CLI wallet" in result.stdout
