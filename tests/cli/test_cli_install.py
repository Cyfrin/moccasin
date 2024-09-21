import os
import subprocess
from pathlib import Path

from tests.conftest import INSTALL_PROJECT_PATH


def test_run_help(mox_path, installation_cleanup_dependencies):
    current_dir = Path.cwd()
    try:
        os.chdir(INSTALL_PROJECT_PATH)
        result = subprocess.run(
            [mox_path, "install", "-h"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "Moccasin CLI install" in result.stdout
