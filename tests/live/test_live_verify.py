import os
import subprocess
from pathlib import Path

import pytest

from tests.conftest import COMPLEX_PROJECT_PATH


@pytest.mark.skip
def test_zksync_verify(mox_path):
    current_dir = Path.cwd()
    try:
        os.chdir(COMPLEX_PROJECT_PATH)
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
