from argparse import Namespace
import os
import tomli_w
import subprocess
import re
from gaboon.config import Config, get_config, initialize_global_config
from gaboon.constants.vars import (
    REQUEST_HEADERS,
    PACKAGE_VERSION_FILE,
    DEPENDENCIES_FOLDER,
)
from base64 import b64encode
import requests
from tqdm import tqdm
import shutil
import zipfile
from io import BytesIO
from gaboon.logging import logger
from urllib.parse import quote
import tomllib


def main(args: Namespace):
    if args.package_name is None:
        _install_dependencies()
    else:
        _pip_install(args.package_name, args.verbose)


def _install_dependencies():
    config = get_config()
    dependencies = config.get_dependencies()
    for package_id in dependencies:
        _pip_install(package_id)


def _pip_install(package_id: str, verbose: bool = False) -> str:
    project_root = Config.find_project_root()
    base_install_path = project_root / DEPENDENCIES_FOLDER
    base_install_path.mkdir(exist_ok=True)

    # TODO: Allow for multiple versions of the same package to be installed
    cmd = ["pip", "install", package_id, "-t", str(base_install_path)]

    # TODO: report which version of the package has been installed
    # TODO: `--upgrade` and `--force` options.
    capture_output = not verbose
    subprocess.run(cmd, capture_output=capture_output, check=True)

    _add_package_to_config(package_id)


def _add_package_to_config(package_id: str) -> None:
    config = get_config()
    dependencies = config.get_dependencies()
    if package_id not in dependencies:
        logger.debug(f"Adding package_id to dependencies")
        dependencies.append(package_id)
        config.write_dependencies(dependencies)
