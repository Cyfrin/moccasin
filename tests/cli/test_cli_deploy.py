import os
import subprocess
from pathlib import Path

from tests.constants import COMPLEX_PROJECT_PATH
from tests.utils.path_utils import restore_original_path_in_error


# --------------------------------------------------------------
#                         WITHOUT ANVIL
# --------------------------------------------------------------
def test_deploy_price_feed_pyevm(mox_path, complex_temp_path, complex_project_config):
    current_dir = Path.cwd()
    try:
        os.chdir(complex_temp_path)
        result = subprocess.run(
            [mox_path, "deploy", "price_feed"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception as e:
        raise restore_original_path_in_error(e, complex_temp_path, COMPLEX_PROJECT_PATH)
    finally:
        os.chdir(current_dir)
    assert "Deployed contract price_feed on pyevm to" in result.stderr


# --------------------------------------------------------------
#                           WITH ANVIL
# --------------------------------------------------------------
def test_deploy_price_feed_anvil(mox_path, complex_temp_path, anvil):
    current_dir = Path.cwd()
    try:
        os.chdir(complex_temp_path)
        result = subprocess.run(
            [mox_path, "deploy", "price_feed", "--network", "anvil"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception as e:
        raise restore_original_path_in_error(e, complex_temp_path, COMPLEX_PROJECT_PATH)
    finally:
        os.chdir(current_dir)
    assert "Deployed contract price_feed on anvil to" in result.stderr
