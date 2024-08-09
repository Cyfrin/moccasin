from pathlib import Path
import subprocess
from gaboon.logging import logger
from gaboon.config import Config, get_config
from gaboon.constants.vars import DEPENDENCIES_FOLDER

def get_base_install_path():
    project_root = Config.find_project_root()
    base_install_path = project_root / DEPENDENCIES_FOLDER
    base_install_path.mkdir(exist_ok=True)
    return base_install_path


def freeze_dependencies():
    base_install_path = get_base_install_path()

    # TODO: switch to uv for this command once they support `--path` option
    # (tracked at https://github.com/astral-sh/uv/issues/5952)
    cmd = ["pip", "freeze", "--path", str(base_install_path)]
    poutput = subprocess.run(cmd, capture_output=True, check=True, text=True)
    dependencies = poutput.stdout.splitlines()
    if len(dependencies):
        logger.info("Installed packages:")
    else:
        logger.info("No installed packages.")
    for pkg in dependencies:
        logger.info(f"- {pkg}")

    config = get_config()
    config.write_dependencies(dependencies)
