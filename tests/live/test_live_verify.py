import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skip
def test_zksync_verify(
    mox_path,
    complex_temp_path,
    complex_cleanup_dependencies_folder,
    complex_cleanup_out_folder,
):
    current_dir = Path.cwd()
    try:
        os.chdir(complex_temp_path)
        result = subprocess.run(
            [
                mox_path,
                "run",
                "deploy_and_verify",
                "--network",
                "sepolia-zksync",
                "--account",
                "smalltestnet",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(current_dir)
    assert "Counter verified" in result.stdout
