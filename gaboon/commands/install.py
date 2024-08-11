from argparse import Namespace
import os
import tomli_w
import subprocess
import re
from packaging.requirements import Requirement
from gaboon.config import Config, get_config, initialize_global_config
from gaboon._dependency_helpers import get_base_install_path
from gaboon.constants.vars import (
    REQUEST_HEADERS,
    PACKAGE_VERSION_FILE,
    DEPENDENCIES_FOLDER,
)
from pathlib import Path
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
    requirements = args.requirements
    if len(requirements) == 0:
        requirements = get_config().get_dependencies()

    _pip_install(requirements, args.verbose)


def _pip_install(package_ids: list[str], verbose: bool = False) -> str:
    path = get_base_install_path()

    # TODO: Allow for multiple versions of the same package to be installed
    cmd = ["uv", "pip", "install", *package_ids, "--target", str(path)]

    # TODO: report which version of the package has been installed
    # TODO: `--upgrade` and `--force` options.
    capture_output = not verbose
    subprocess.run(cmd, capture_output=capture_output, check=True)

    config = get_config()
    dependencies = config.get_dependencies()

    to_delete = set()
    for package in package_ids:
        for dep in dependencies:
            if Requirement(dep).name == Requirement(package).name:
                to_delete.add(dep)
        logger.info(f"Installed {package}")

    dependencies = [dep for dep in dependencies if dep not in to_delete]
    # TODO: keep original order of dependencies
    # e.g. if gaboon.toml has snekmate==0.1.0 and user installs
    # snekmate==0.2.0, we should keep the original order in the toml file.
    dependencies.extend(package_ids)

    config.write_dependencies(dependencies)
