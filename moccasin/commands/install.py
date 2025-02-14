import re
import shutil
import subprocess
import sys
import traceback
import zipfile
from argparse import Namespace
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import requests
from packaging.requirements import Requirement
from tqdm import tqdm

from moccasin._dependency_utils import (
    DependencyType,
    GitHubDependency,
    get_new_or_updated_dependencies,
    parse_and_convert_dependencies,
    write_dependency_to_versions_file,
    write_new_config_dependencies,
)
from moccasin.config import get_or_initialize_config
from moccasin.constants.vars import GITHUB, PACKAGE_VERSION_FILE, PYPI, REQUEST_HEADERS
from moccasin.logging import logger, set_log_level


def main(args: Namespace) -> int:
    """
    Main entry point for the install command.

    :param args: Command line arguments
    :type args: Namespace
    :return: Exit code (0 for success)
    :rtype: int
    """
    # Force quiet and update-packages flags for install
    # @dev see if we want them to be set by default or not
    args.quiet = False
    args.update_packages = True
    return mox_install(args)


def mox_install(args: Namespace | None = None) -> int:
    """
    Install the given requirements from PyPI and GitHub.

    If no requirements are given, install all requirements in the config file.
    This command is used for install, compile and deploy commands.

    :param args: Namespace containing the requirements to install
    :type args: Namespace | None
    :return: Exit code (0 for success)
    :rtype: int

    .. note::
        The function will:
        * Install new packages that are not in versions.toml
        * Update existing packages that need version updates
        * Handle both PyPI and GitHub dependencies
    """
    # Get config base install path
    config = get_or_initialize_config()
    config_dependencies = config.get_dependencies()
    base_install_path: Path = config.get_base_dependencies_install_path()

    # Get pip and github paths
    pip_install_path = base_install_path.joinpath(PYPI)
    github_install_path = base_install_path.joinpath(GITHUB)

    # Get requirements
    requested_dependencies: list[str] = (
        args.requirements if args is not None and hasattr(args, "requirements") else []
    )

    # Return early if no requirements are given
    if len(requested_dependencies) == 0 and len(config_dependencies) == 0:
        logger.info("No packages to install.")
        return 0

    # Get quiet flag and set log level
    quiet = args.quiet if hasattr(args, "quiet") else False
    set_log_level(quiet=quiet)
    # Get update-packages flag
    update_packages = (
        args.update_packages if hasattr(args, "update_packages") else False
    )

    # Parse dependencies and convert to pip and github requirements
    logger.info("Parsing requirements...")
    requirements_dict = parse_and_convert_dependencies(
        config_dependencies, requested_dependencies
    )

    # Get pip and github requirements
    logger.info("Checking for new or to update packages...")
    pip_new_or_updated, github_new_or_updated = get_new_or_updated_dependencies(
        requirements_dict, pip_install_path, github_install_path, update_packages
    )

    # Pip installs
    if len(pip_new_or_updated) > 0:
        _pip_installs(pip_new_or_updated, pip_install_path, quiet)
    else:
        logger.info("No pip packages to install")

    # Github installs
    if len(github_new_or_updated) > 0:
        logger.info("Checking for new or to update GitHub packages...")
        _github_installs(github_new_or_updated, github_install_path)
    else:
        logger.info("No GitHub packages to install")

    # Reset log level
    set_log_level()
    return 0


# ------------------------------------------------------------------
#                           PIP INSTALL
# ------------------------------------------------------------------
def _pip_installs(
    new_pip_packages: list[Requirement], base_install_path: Path, quiet: bool = False
):
    """
    Install the given pip packages using uv package manager.

    :param new_pip_packages: List of pip packages to install
    :type new_pip_packages: list[Requirement]
    :param base_install_path: Path to install the packages
    :type base_install_path: Path
    :param quiet: Flag to suppress installation output
    :type quiet: bool
    :raises FileNotFoundError: If uv package manager is not found
    :raises subprocess.CalledProcessError: If package installation fails

    .. note::
        This function will:
        * Install packages using uv package manager
        * Update the versions file with new package versions
        * Update the configuration with new dependencies
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
        write_dependency_to_versions_file(versions_install_path, package)

    write_new_config_dependencies(new_pip_packages, DependencyType.PIP)


# ------------------------------------------------------------------
#                            GH INSTALL
# ------------------------------------------------------------------
def _github_installs(
    github_new_or_updated: list[GitHubDependency], base_install_path: Path
):
    """
    Install the given GitHub packages by downloading and extracting zip archives.

    :param github_new_or_updated: List of GitHub packages to install
    :type github_new_or_updated: list[GitHubDependency]
    :param base_install_path: Path to install the packages
    :type base_install_path: Path
    :raises ConnectionError: If download URL is invalid or inaccessible
    :raises requests.exceptions.HTTPError: If GitHub API request fails

    .. note::
        This function will:
        * Download repository as zip from GitHub
        * Extract to the specified installation path
        * Handle special characters in version tags
        * Update the versions file and configuration
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
        write_dependency_to_versions_file(versions_install_path, github_dependency)

    write_new_config_dependencies(github_new_or_updated, DependencyType.GITHUB)


def _stream_download(
    download_url: str, target_path: str, headers: dict[str, str] = REQUEST_HEADERS
) -> None:
    """
    Download a file from URL with progress bar.

    :param download_url: URL to download from
    :type download_url: str
    :param target_path: Path to save the downloaded file
    :type target_path: str
    :param headers: Request headers (default: REQUEST_HEADERS)
    :type headers: dict[str, str]
    :raises requests.exceptions.HTTPError: If download fails

    .. note::
        Uses tqdm to show download progress with size in bytes
    """
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
    """
    Get the download URL for a GitHub repository tag.

    :param org: GitHub organization/owner name
    :type org: str
    :param repo: Repository name
    :type repo: str
    :param version: Version tag to download
    :type version: str
    :param headers: GitHub API request headers
    :type headers: dict
    :return: Download URL for the repository zip
    :rtype: str
    :raises requests.exceptions.HTTPError: If GitHub API request fails
    :raises ValueError: If version tag is not found

    .. note::
        Uses GitHub API to get the download URL for a specific tag
    """
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
