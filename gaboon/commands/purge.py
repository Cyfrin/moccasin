from argparse import Namespace
import os
import tomli_w
import subprocess
import re
from gaboon._dependency_helpers import freeze_dependencies, get_base_install_path
from gaboon.config import Config, get_config, initialize_global_config
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
    _purge(args.packages, args.verbose)

def _purge(packages: list[str], verbose: bool = False) -> str:
    path = get_base_install_path()
    # TODO: Allow for multiple versions of the same package to be installed
    cmd = ["uv", "pip", "uninstall", *packages, "--target", str(path)]

    # TODO: report which version of the package has been installed
    # TODO: `--upgrade` and `--force` options.
    capture_output = not verbose
    subprocess.run(cmd, capture_output=capture_output, check=True)

    for package in packages:
        logger.info(f"Removed {package}")

    # freeze dependencies
    freeze_dependencies()
