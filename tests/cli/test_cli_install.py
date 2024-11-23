import os
import subprocess
from pathlib import Path


def test_run_help(mox_path, installation_cleanup_dependencies, installation_temp_path):
    current_dir = Path.cwd()
    try:
        os.chdir(installation_temp_path)
        result = subprocess.run(
            [mox_path, "install", "-h"], check=True, capture_output=True, text=True
        )
    finally:
        os.chdir(current_dir)
    assert "Moccasin CLI install" in result.stdout
