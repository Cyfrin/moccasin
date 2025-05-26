import os
import re
import shutil
import subprocess
import sys
import tomllib
import traceback
import zipfile
from argparse import Namespace
from base64 import b64encode
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import requests  # type: ignore
import tomli_w
from packaging.requirements import Requirement
from packaging.version import parse as parse_version
from tqdm import tqdm

from moccasin._dependency_utils import (
    DependencyType,
    _write_new_dependencies,
    classify_dependency,
)
from moccasin.config import get_or_initialize_config
from moccasin.constants.vars import GITHUB, PACKAGE_VERSION_FILE, PYPI, REQUEST_HEADERS
from moccasin.logging import logger, set_log_level


def main(args: Namespace):
    requirements = args.requirements if hasattr(args, "requirements") else []
    no_install = args.no_install if hasattr(args, "no_install") else False
    quiet = args.quiet if hasattr(args, "quiet") else False
    debug = args.debug if hasattr(args, "debug") else False
    return mox_install(
        requirements=requirements,
        no_install=no_install,
        quiet=quiet,
        debug=debug,
        override_logger=False,
    )


def mox_install(
    requirements=[],
    no_install=None,
    config=None,
    quiet=False,
    debug=False,
    override_logger=False,
):
    """@dev IMPORTANT, this function can override the logger level, it's good to
    reset it after calling this function.
    """
    if quiet:
        set_log_level(quiet=quiet, debug=debug)
    if no_install:
        return 0
    if config is None:
        config = get_or_initialize_config()
    if len(requirements) == 0:
        requirements = config.get_dependencies()

    # Get dependencies install path and create it if it doesn't exist
    # @dev allows to avoid vyper compiler error when missing one dir
    install_path: Path = config.get_base_dependencies_install_path()
    install_path.joinpath(PYPI).mkdir(exist_ok=True, parents=True)
    install_path.joinpath(GITHUB).mkdir(exist_ok=True, parents=True)
    if len(requirements) == 0:
        logger.info("No dependencies to install.")
        return 0

    pip_requirements = []
    github_requirements = []
    for requirement in requirements:
        if classify_dependency(requirement) == DependencyType.GITHUB:
            github_requirements.append(requirement)
        else:
            pip_requirements.append(requirement)

    # @dev in case of fresh install, dependencies might be ordered differently
    # since we install pip packages first and github packages later
    # @dev see _dependency_utils._write_new_dependencies
    if len(pip_requirements) > 0:
        _pip_installs(
            pip_requirements, install_path.joinpath(PYPI), quiet, override_logger
        )
    if len(github_requirements) > 0:
        _github_installs(
            github_requirements, install_path.joinpath(GITHUB), quiet, override_logger
        )
    return 0


# Much of this code thanks to brownie
# https://github.com/eth-brownie/brownie/blob/master/brownie/_config.py
def _github_installs(
    github_ids: list[str],
    base_install_path: Path,
    quiet: bool = False,
    override_logger=False,
):
    logger.info(f"Installing {len(github_ids)} GitHub packages...")
    for package_id in github_ids:
        try:
            if "@" in package_id:
                path, version = package_id.split("@", 1)
            else:
                path = package_id
                version = None  # We'll fetch the latest version later
            org, repo = path.split("/")
            org = org.strip().lower()
            repo = repo.strip().lower()
        except ValueError:
            raise ValueError(
                "Invalid package ID. Must be given as ORG/REPO[@VERSION]"
                "\ne.g. 'pcaversaccio/snekmate@v2.5.0'"
            ) from None

        headers = REQUEST_HEADERS.copy()
        headers.update(_maybe_retrieve_github_auth())

        if version is None:
            version = _get_latest_version(org, repo, headers)
            logger.info(f"Using latest version for {org}/{repo}: {version}")

        org_install_path = base_install_path.joinpath(f"{org}")
        org_install_path.mkdir(exist_ok=True, parents=True)
        repo_install_path = org_install_path.joinpath(f"{repo}")
        versions_install_path = base_install_path.joinpath(PACKAGE_VERSION_FILE)

        if repo_install_path.exists():
            with open(versions_install_path, "rb") as f:
                versions = tomllib.load(f)
                versions = {k.lower(): v for k, v in versions.items()}
                installed_version = versions.get(f"{org}/{repo}", None)
            if installed_version == version:
                logger.info(f"{org}/{repo} already installed at version {version}")
                continue
            else:
                if override_logger:
                    set_log_level(quiet=False)
                logger.info(
                    f"Updating {org}/{repo} from {installed_version} to {version}"
                )

        if re.match(r"^[0-9a-f]+$", version):
            download_url = (
                f"https://api.github.com/repos/{org}/{repo}/zipball/{version}"
            )
        else:
            download_url = _get_download_url_from_tag(org, repo, version, headers)
        existing = list(repo_install_path.parent.iterdir())

        # Some versions contain special characters and github api seems to display url without
        # encoding them.
        # It results in a ConnectionError exception because the actual download url is encoded.
        # In this case we try to sanitize the version in url and download again.
        try:
            _stream_download(download_url, str(repo_install_path.parent), headers)
        except ConnectionError:
            download_url = f"https://api.github.com/repos/{org}/{repo}/zipball/refs/tags/{quote(version)}"
            _stream_download(download_url, str(repo_install_path.parent), headers)

        try:
            installed = next(
                i for i in repo_install_path.parent.iterdir() if i not in existing
            )
        except StopIteration:
            installed = None

        if installed:
            if repo_install_path.exists():
                shutil.rmtree(repo_install_path)
            shutil.move(installed, repo_install_path)

        # Update versions file
        if versions_install_path.exists():
            with open(versions_install_path, "rb") as f:
                versions_data = tomllib.load(f)
            versions_data[f"{org}/{repo}"] = version
            with open(versions_install_path, "wb") as f:
                tomli_w.dump(versions_data, f)
        else:
            with open(versions_install_path, "w", encoding="utf-8") as f:
                toml_string = tomli_w.dumps({f"{org}/{repo}": version})
                f.write(toml_string)
        _write_new_dependencies(github_ids, DependencyType.GITHUB)


def _get_latest_version(org: str, repo: str, headers: dict) -> str:
    response = requests.get(
        f"https://api.github.com/repos/{org}/{repo}/releases/latest", headers=headers
    )
    if response.status_code == 200:
        return response.json()["tag_name"].lstrip("v")

    response = requests.get(
        f"https://api.github.com/repos/{org}/{repo}/tags?per_page=1", headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]["name"].lstrip("v")

    raise ValueError(f"Unable to determine latest version for {org}/{repo}")


def _stream_download(
    download_url: str, target_path: str, headers: dict[str, str] = REQUEST_HEADERS
) -> None:
    response = requests.get(download_url, stream=True, headers=headers)

    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))
    progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)
    content = bytes()

    for data in response.iter_content(None, decode_unicode=True):
        progress_bar.update(len(data))
        content += data
    progress_bar.close()

    with zipfile.ZipFile(BytesIO(content)) as zf:
        zf.extractall(target_path)


def _maybe_retrieve_github_auth() -> dict[str, str]:
    """Returns appropriate github authorization headers.

    Otherwise returns an empty dict if no auth token is present.
    """
    token = os.getenv("GITHUB_TOKEN")
    if token is not None:
        auth = b64encode(token.encode()).decode()
        return {"Authorization": f"Basic {auth}"}
    return {}


def _get_download_url_from_tag(org: str, repo: str, version: str, headers: dict) -> str:
    response = requests.get(
        f"https://api.github.com/repos/{org}/{repo}/tags?per_page=100", headers=headers
    )
    response.raise_for_status()

    data = response.json()
    if not data:
        raise ValueError("Github repository has no tags set")

    available_versions = []
    for tag in data:
        tag_version = tag["name"].lstrip("v")
        available_versions.append(tag_version)
        if tag_version == version:
            return tag["zipball_url"]

    # If we've gone through all tags without finding a match, raise an error
    raise ValueError(
        f"Invalid version '{version}' for this package. Available versions are:\n"
        + ", ".join(available_versions)
    )


def _pip_installs(
    package_ids: list[str],
    base_install_path: Path,
    quiet: bool = False,
    override_logger=False,
):
    logger.info(f"Installing {len(package_ids)} pip packages...")

    # Check if they are already installed on the right version
    packages_to_install = []
    for package_id in package_ids:
        name, version_spec = parse_package_req(package_id)

        if base_install_path.joinpath(name).exists():
            dist_info = next(base_install_path.glob(f"{name}-*.dist-info"))
            installed_version = dist_info.name.replace(f"{name}-", "").replace(
                ".dist-info", ""
            )

            if version_spec:
                if not version_spec.contains(parse_version(installed_version)):
                    logger.info(
                        f"{name} {installed_version} installed but {package_id} required."
                    )
                    packages_to_install.append(package_id)
                    continue
        else:
            packages_to_install.append(package_id)

    if len(packages_to_install) == 0:
        logger.info("All packages already installed.")
        return 0

    if override_logger:
        set_log_level(quiet=False)

    cmd = [
        "uv",
        "pip",
        "install",
        *packages_to_install,
        "--target",
        str(base_install_path),
    ]

    capture_output = quiet
    try:
        subprocess.run(cmd, capture_output=capture_output, check=True)
    except FileNotFoundError as e:
        logger.info(
            f"Stack trace:\n{''.join(traceback.format_exception(type(e), e, e.__traceback__))}"
        )
        sys.exit(1)

    _write_new_dependencies(package_ids, DependencyType.PIP)


def parse_package_req(package_id):
    req = Requirement(package_id)
    return req.name, next(iter(req.specifier)) if req.specifier else None
