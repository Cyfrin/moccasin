import re
import shutil
import subprocess
import sys
import traceback
import zipfile
from argparse import Namespace
from io import BytesIO
from packaging.requirements import Requirement
from pathlib import Path
from urllib.parse import quote

import requests  # type: ignore
from tqdm import tqdm

from moccasin._dependency_utils import (
    DependencyType,
    GitHubDependency,
    add_dependency_to_versions_file,
    write_new_config_dependencies,
    get_dependencies,
    get_new_or_updated_github_dependencies,
    get_new_or_updated_pip_dependencies,
)
from moccasin.config import get_or_initialize_config
from moccasin.constants.vars import GITHUB, PACKAGE_VERSION_FILE, PYPI, REQUEST_HEADERS
from moccasin.logging import logger


def main(args: Namespace) -> int:
    return mox_install(args)


def mox_install(args: Namespace | None = None) -> int:
    """Install the given requirements from PyPI and GitHub.

    If no requirements are given, install all requirements in the config file.

    @dev This command is used for install, compile and deploy commands.

    :param args: Namespace containing the requirements to install
    :type args: Namespace
    :return: int 0 at the end of the function
    :rtype: int
    """
    # Get config dependencies and requirements
    config_dependencies = get_or_initialize_config().get_dependencies()
    if (
        args is not None
        and hasattr(args, "requirements")
        and len(args.requirements) > 0
    ):
        project_requirements = (
            list(set(args.requirements + config_dependencies))
            if args.requirements
            else config_dependencies
        )
    else:
        project_requirements = config_dependencies

    # Get quiet flag
    quiet = args.quiet if hasattr(args, "quiet") else False

    # Get pip and github requirements
    pip_requirements, github_requirements = get_dependencies(project_requirements)
    install_path: Path = get_or_initialize_config().get_base_dependencies_install_path()

    # Pip installs
    if len(pip_requirements) > 0:
        logger.info("Checking for new or to update pip packages...")
        new_pip_packages = get_new_or_updated_pip_dependencies(
            pip_requirements, install_path.joinpath(PYPI)
        )
        if len(new_pip_packages) > 0:
            _pip_installs(new_pip_packages, install_path.joinpath(PYPI), quiet)
        else:
            logger.info("No new or updated pip packages to install")
    else:
        logger.info("No pip packages to install")

    # Github installs
    if len(github_requirements) > 0:
        logger.info("Checking for new or to update GitHub packages...")
        new_github_packages = get_new_or_updated_github_dependencies(
            github_requirements, install_path.joinpath(GITHUB)
        )
        if len(new_github_packages) > 0:
            _github_installs(new_github_packages, install_path.joinpath(GITHUB))
        else:
            logger.info("No new or updated GitHub packages to install")
    else:
        logger.info("No GitHub packages to install")
    return 0


# ------------------------------------------------------------------
#                           PIP INSTALL
# ------------------------------------------------------------------
def _pip_installs(
    new_pip_packages: list[Requirement], base_install_path: Path, quiet: bool = False
):
    """Install the given pip packages.

    :param new_pip_packages: list of pip packages to install
    :type new_pip_packages: list[Requirement]
    :param base_install_path: path to install the packages
    :type base_install_path: Path
    :param quiet: flag to install packages quietly
    :type quiet: bool
    """
    logger.info(f"Installing {len(new_pip_packages)} pip packages...")
    cmd = [
        "uv",
        "pip",
        "install",
        *[str(req) for req in new_pip_packages],  # @dev could be better
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

    versions_install_path = base_install_path.joinpath(PACKAGE_VERSION_FILE)
    # @dev Could be better here maybe
    for package in new_pip_packages:
        add_dependency_to_versions_file(versions_install_path, package)

    write_new_config_dependencies(new_pip_packages, DependencyType.PIP)


# ------------------------------------------------------------------
#                            GH INSTALL
# ------------------------------------------------------------------
def _github_installs(
    github_new_or_updated: list[GitHubDependency], base_install_path: Path
):
    """Install the given GitHub packages.

    :param github_new_or_updated: list of GitHub packages to install
    :type github_new_or_updated: list[GitHubDependency]
    :param base_install_path: path to install the packages
    :type base_install_path: Path
    """
    logger.info(f"Installing {len(github_new_or_updated)} GitHub packages...")
    for github_dependency in github_new_or_updated:
        if re.match(r"^[0-9a-f]+$", github_dependency.version):
            download_url = f"https://api.github.com/repos/{github_dependency.org}/{github_dependency.repo}/zipball/{github_dependency.version}"
        else:
            download_url = _get_download_url_from_tag(
                github_dependency.org,
                github_dependency.repo,
                github_dependency.version,
                github_dependency.headers,
            )

        org_install_path = base_install_path.joinpath(f"{github_dependency.org}")
        org_install_path.mkdir(exist_ok=True, parents=True)
        repo_install_path = org_install_path.joinpath(f"{github_dependency.repo}")
        versions_install_path = base_install_path.joinpath(PACKAGE_VERSION_FILE)

        existing = list(repo_install_path.parent.iterdir())

        # Some versions contain special characters and github api seems to display url without
        # encoding them.
        # It results in a ConnectionError exception because the actual download url is encoded.
        # In this case we try to sanitize the version in url and download again.
        try:
            _stream_download(
                download_url, str(repo_install_path.parent), github_dependency.headers
            )
        except ConnectionError:
            download_url = f"https://api.github.com/repos/{github_dependency.org}/{github_dependency.repo}/zipball/refs/tags/{quote(github_dependency.version)}"
            _stream_download(
                download_url, str(repo_install_path.parent), github_dependency.headers
            )

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
        add_dependency_to_versions_file(versions_install_path, github_dependency)

    write_new_config_dependencies(github_new_or_updated, DependencyType.GITHUB)


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
