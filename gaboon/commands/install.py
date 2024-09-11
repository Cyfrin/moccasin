from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from packaging.requirements import Requirement
from gaboon.config import get_config
from gaboon.logging import logger
import os
from base64 import b64encode
import re
import requests
import sys
import traceback
from tqdm import tqdm
import zipfile
from io import BytesIO
from gaboon.constants.vars import (
    REQUEST_HEADERS,
    PACKAGE_VERSION_FILE,
)
import tomllib
import tomli_w
from enum import Enum
from urllib.parse import quote


class DependencyType(Enum):
    GITHUB = "github"
    PIP = "pip"


def main(args: Namespace):
    requirements = args.requirements
    config = get_config()
    if len(requirements) == 0:
        requirements = config.get_dependencies()
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
    install_path: Path = config.get_base_dependencies_install_path()
    if len(pip_requirements) > 0:
        _pip_installs(pip_requirements, install_path, config.installer, args.quiet)
    if len(github_requirements) > 0:
        _github_installs(github_requirements, install_path, args.quiet)
    return 0


def classify_dependency(dependency: str) -> DependencyType:
    # GitHub dependency pattern
    github_pattern = r"^([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)(@[a-zA-Z0-9_.-]+)?$"

    if re.match(github_pattern, dependency):
        return DependencyType.GITHUB

    return DependencyType.PIP


# Much of this code thanks to brownie
# https://github.com/eth-brownie/brownie/blob/master/brownie/_config.py
def _github_installs(
    github_ids: list[str], base_install_path: Path, quiet: bool = False
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
        except ValueError:
            raise ValueError(
                "Invalid package ID. Must be given as ORG/REPO@[VERSION]"
                "\ne.g. 'pcaversaccio/snekmate@v2.5.0'"
            ) from None

        headers = REQUEST_HEADERS.copy()
        headers.update(_maybe_retrieve_github_auth())

        if version is None:
            version = _get_latest_version(org, repo, headers)
            logger.info(f"Using latest version for {org}/{repo}: {version}")

        org_install_path = base_install_path.joinpath(f"{org}")
        org_install_path.mkdir(exist_ok=True)
        repo_install_path = org_install_path.joinpath(f"{repo}")
        versions_install_path = base_install_path.joinpath(PACKAGE_VERSION_FILE)

        # TODO: Allow for multiple versions of the same package to be installed
        if repo_install_path.exists():
            with open(versions_install_path, "rb") as f:
                versions = tomllib.load(f)
                installed_version = versions.get(f"{org}/{repo}", None)
            if installed_version == version:
                logger.info(f"Installed {org}/{repo}")
                _write_dependencies([f"{org}/{repo}@{version}"], DependencyType.GITHUB)
                return f"{org}/{repo}@{version}"
            else:
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

        installed = next(
            i for i in repo_install_path.parent.iterdir() if i not in existing
        )
        shutil.move(installed, repo_install_path)

        # Update versions file
        if versions_install_path.exists():
            with open(versions_install_path, "rb") as f:
                versions_data = tomllib.load(f)
                versions_data[f"{org}/{repo}"] = version
                tomli_w.dump(versions_data, f)
        else:
            with open(versions_install_path, "w", encoding="utf-8") as f:
                toml_string = tomli_w.dumps({f"{org}/{repo}": version})
                f.write(toml_string)
        _write_dependencies(github_ids, DependencyType.GITHUB)


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


import requests
from tqdm import tqdm
import zipfile
import os


def _stream_download(
    download_url: str, target_path: str, headers: dict[str, str] = REQUEST_HEADERS
) -> None:
    with requests.get(download_url, stream=True, headers=headers) as response:
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0))

        temp_file = os.path.join(target_path, "temp_download.zip")

        with open(temp_file, "wb") as f, tqdm(
            desc="Downloading",
            total=total_size,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
        ) as progress_bar:
            for data in response.iter_content(chunk_size=8192):
                size = f.write(data)
                progress_bar.update(size)

        with zipfile.ZipFile(temp_file, "r") as zip_ref:
            zip_ref.extractall(target_path)

        os.remove(temp_file)


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
    package_ids: list[str], base_install_path: Path, installer: str, quiet: bool = False
):
    logger.info(f"Installing {len(package_ids)} pip packages...")
    cmd = []
    # TODO: Allow for multiple versions of the same package to be installed
    if installer == "uv":
        cmd = ["uv", "pip", "install", *package_ids, "--target", str(base_install_path)]
    else:
        cmd = ["pip", "install", *package_ids, "--target", str(base_install_path)]

    # TODO: `--upgrade` and `--force` options.
    capture_output = quiet
    try:
        subprocess.run(cmd, capture_output=capture_output, check=True)
    except FileNotFoundError as e:
        logger.info(
            f"Stack trace:\n{''.join(traceback.format_exception(type(e), e, e.__traceback__))}"
        )
        logger.error(e)
        logger.info(
            f'Your installer {installer} is not found in your system PATH.\nPlease install {installer} or update your installer in your gaboon.toml as: \n\n[project]\ninstaller = "your installer here (pip or uv)"'
        )
        sys.exit(1)

    _write_dependencies(package_ids, DependencyType.PIP)


def _write_dependencies(new_package_ids: list[str], dependency_type: DependencyType):
    config = get_config()
    dependencies = config.get_dependencies()
    typed_dependencies = [
        dep for dep in dependencies if classify_dependency(dep) == dependency_type
    ]

    to_delete = set()
    updated_packages = set()

    if dependency_type == DependencyType.PIP:
        for package in new_package_ids:
            package_req = Requirement(package)
            for dep in typed_dependencies:
                dep_req = Requirement(dep)
                if dep_req.name == package_req.name:
                    to_delete.add(dep)
                    updated_packages.add(package_req.name)

            if package_req.name not in updated_packages:
                logger.info(f"Installed new package: {package}")
            else:
                logger.info(f"Updated package: {package}")
    else:  # GIT dependencies
        for package in new_package_ids:
            package_dep = GitHubDependency.from_string(package)
            for dep in typed_dependencies:
                dep_gh = GitHubDependency.from_string(dep)
                if dep_gh.org == package_dep.org and dep_gh.repo == package_dep.repo:
                    to_delete.add(dep)
                    updated_packages.add(f"{package_dep.org}/{package_dep.repo}")

            if f"{package_dep.org}/{package_dep.repo}" not in updated_packages:
                logger.info(f"Installed {package}")
            else:
                logger.info(f"Updated {package}")

    # Remove old versions of updated packages
    dependencies = [dep for dep in dependencies if dep not in to_delete]

    # Add new packages while preserving order
    new_deps = []
    for dep in dependencies + new_package_ids:
        if dep not in new_deps:
            new_deps.append(dep)

    config.write_dependencies(new_deps)


@dataclass
class GitHubDependency:
    org: str
    repo: str
    version: str | None = None

    @classmethod
    def from_string(cls, dep_string: str) -> "GitHubDependency":
        path, version = (
            dep_string.split("@", 1) if "@" in dep_string else (dep_string, None)
        )
        org, repo = str(path).split("/")
        return cls(org, repo, version)

    def __str__(self) -> str:
        if self.version:
            return f"{self.org}/{self.repo}@{self.version}"
        return f"{self.org}/{self.repo}"
