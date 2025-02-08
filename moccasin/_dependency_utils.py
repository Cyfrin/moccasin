import os
import re
import requests  # type: ignore
import tomllib
import tomli_w

from base64 import b64encode
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Tuple
from packaging.requirements import InvalidRequirement, Requirement, SpecifierSet

from moccasin.constants.vars import PACKAGE_VERSION_FILE, REQUEST_HEADERS
from moccasin.config import get_or_initialize_config
from moccasin.logging import logger


class DependencyType(Enum):
    GITHUB = "github"
    PIP = "pip"


# ------------------------------------------------------------------
#                       HANDLE DEPENDENCIES
# ------------------------------------------------------------------
def classify_dependency(dependency: str) -> DependencyType:
    dependency = dependency.strip().strip("'\"")

    github_shorthand = r"^([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)(@[a-zA-Z0-9_.-]+)?$"
    github_url = r"^https://github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$"

    if re.match(github_shorthand, dependency) or re.match(github_url, dependency):
        return DependencyType.GITHUB

    return DependencyType.PIP


def get_dependencies(requirements: list[str]) -> Tuple[list[str], list[str]]:
    """Return a tuple with the pip and github dependencies.

    :param requirements: List of requirements to parse
    :type requirements: list[str]
    :return: Tuple with the pip and github dependencies
    :rtype: Tuple[list[str], list[str]]
    """
    # Init dependencies lists
    pip_dependencies = []
    github_dependencies = []

    # Check if we have any requirements to parse
    if len(requirements) == 0:
        requirements = get_or_initialize_config().get_dependencies()
    if len(requirements) == 0:
        # If we have no requirements, return dict with empty lists
        return (pip_dependencies, github_dependencies)

    # Populate requirements lists
    for requirement in requirements:
        if classify_dependency(requirement) == DependencyType.GITHUB:
            github_dependencies.append(requirement)
        else:
            pip_dependencies.append(requirement)

    return (pip_dependencies, github_dependencies)


# ------------------------------------------------------------------
#                         PIP DEPENDENCIES
# ------------------------------------------------------------------
def get_new_or_updated_pip_dependencies(
    pip_packages: list[str], base_install_path: Path
) -> list[Requirement]:
    """Return a list of new or updated pip packages.

    :param pip_packages: List of pip packages with optional version specifiers
    :type pip_packages: list[str]
    :param base_install_path: Base install path
    :type base_install_path: Path
    :return: List of new or updated pip packages
    :rtype: list[Requirement]
    """
    new_or_updated = []

    versions_install_path = base_install_path.joinpath(PACKAGE_VERSION_FILE)
    if not versions_install_path.exists():
        # If versions file doesn't exist, all packages need to be installed
        for package in pip_packages:
            try:
                # Preprocess package name
                processed_package = preprocess_requirement(package)
                package_req = Requirement(processed_package)
            except InvalidRequirement:
                logger.warning(f"Invalid requirement format for package: {package}")
                continue
            new_or_updated.append(package_req)
        return new_or_updated

    # If versions file exists, check if packages need to be updated
    with open(versions_install_path, "rb") as f:
        versions = tomllib.load(f)
        versions = {k.lower(): v for k, v in versions.items()}

    for package in pip_packages:
        try:
            processed_package = preprocess_requirement(package)
            package_req = Requirement(processed_package)
        except InvalidRequirement:
            logger.warning(f"Invalid requirement format for package: {package}")
            continue

        package_name = package_req.name

        installed_version = versions.get(package_name.lower())
        if installed_version is None:
            new_or_updated.append(package_req)
            logger.info(f"Package {package_name} not installed")
            continue

        # Extract version number
        version_pattern = re.compile(r"^([\w.-]+)(?:(==|>=|<=|!=|~=|>|<)(.+))?$")
        match = version_pattern.match(installed_version)
        version_operator = match.group(2)
        version_number = match.group(3)

        # If version number doesn't match requirement, package needs to be updated
        if version_number is not None:
            # Convert version number to a SpecifierSet and compare with requirement
            installed_specifier = f"{version_operator}{version_number}"
            if SpecifierSet(installed_specifier) != package_req.specifier:
                new_or_updated.append(package_req)
                logger.info(f"Package {package_name} needs to be updated")
        else:
            if package_req.specifier is not None:
                new_or_updated.append(package_req)
                logger.info(f"Package {package_name} needs to be updated")

    return new_or_updated


# ------------------------------------------------------------------
#                         GH DEPENDENCIES
# ------------------------------------------------------------------
@dataclass
class GitHubDependency:
    org: str
    repo: str
    version: str | None = None
    headers: dict | None = None

    @classmethod
    def from_string(cls, dep_string: str) -> "GitHubDependency":
        try:
            if "@" in dep_string:
                path, version = dep_string.split("@")
            else:
                path, version = dep_string, None

            org, repo = str(path).split("/")
        except ValueError:
            raise ValueError(
                "Invalid package ID. Must be given as ORG/REPO[@VERSION]"
                "\ne.g. 'pcaversaccio/snekmate@v2.5.0'"
            ) from None
        org = org.strip().lower()
        repo = repo.strip().lower()
        version = version.strip() if version else None
        return cls(org, repo, version)

    def format_no_version(self) -> str:
        return f"{self.org}/{self.repo}"

    def __str__(self) -> str:
        if self.version:
            return f"{self.org}/{self.repo}@{self.version}"
        return self.format_no_version()


def get_new_or_updated_github_dependencies(
    github_ids: list[str], base_install_path: Path
):
    """Return a list of new or updated GitHub dependencies.

    :param github_ids: List of GitHub dependency IDs
    :type github_ids: list[str]
    :param base_install_path: Base install path
    :type base_install_path: Path
    :return: List of new or updated GitHub dependencies
    :rtype: list[str]
    """
    new_or_updated = []
    for package_id in github_ids:
        github_dependency = GitHubDependency.from_string(package_id)

        headers = REQUEST_HEADERS.copy()
        headers.update(_maybe_retrieve_github_auth())

        if github_dependency.headers is None:
            github_dependency.headers = headers

        if github_dependency.version is None:
            github_dependency.version = _get_latest_github_version(
                github_dependency.org, github_dependency.repo, github_dependency.headers
            )
            logger.info(
                f"Using latest version for {github_dependency.org}/{github_dependency.repo}: {github_dependency.version}"
            )

        versions_install_path = base_install_path.joinpath(PACKAGE_VERSION_FILE)
        if versions_install_path.exists():
            with open(versions_install_path, "rb") as f:
                versions = tomllib.load(f)
                versions = {k.lower(): v for k, v in versions.items()}
                installed_version = versions.get(
                    f"{github_dependency.org}/{github_dependency.repo}", None
                )
            if installed_version == github_dependency.version:
                logger.info(
                    f"{github_dependency.org}/{github_dependency.repo} already installed at version {github_dependency.version}"
                )
                continue
            else:
                logger.info(
                    f"{github_dependency.org}/{github_dependency.repo} needs to be updated from version {installed_version} to {github_dependency.version}"
                )
                new_or_updated.append(github_dependency)
        else:
            # If versions file doesn't exist, all packages need to be installed
            new_or_updated.append(github_dependency)

    return new_or_updated


def _maybe_retrieve_github_auth() -> dict[str, str]:
    """Returns appropriate github authorization headers.

    Otherwise returns an empty dict if no auth token is present.
    """
    token = os.getenv("GITHUB_TOKEN")
    if token is not None:
        auth = b64encode(token.encode()).decode()
        return {"Authorization": f"Basic {auth}"}
    return {}


def _get_latest_github_version(org: str, repo: str, headers: dict) -> str:
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


# ------------------------------------------------------------------
#                        WRITE DEPENDENCIES
# ------------------------------------------------------------------
def add_dependency_to_versions_file(
    versions_install_path: Path, dependency: GitHubDependency | Requirement
):
    # Update versions file
    if versions_install_path.exists():
        with open(versions_install_path, "rb") as f:
            versions_data = tomllib.load(f)
        if isinstance(dependency, GitHubDependency):
            versions_data[f"{dependency.org}/{dependency.repo}"] = dependency.version
        else:
            versions_data[f"{dependency.name}"] = str(dependency)

        with open(versions_install_path, "wb") as f:
            tomli_w.dump(versions_data, f)
    else:
        with open(versions_install_path, "w", encoding="utf-8") as f:
            if isinstance(dependency, GitHubDependency):
                toml_string = tomli_w.dumps(
                    {f"{dependency.org}/{dependency.repo}": dependency.version}
                )
            else:
                toml_string = tomli_w.dumps({dependency.name: str(dependency)})
            f.write(toml_string)


def write_new_config_dependencies(
    new_package_ids: list[GitHubDependency | Requirement],
    dependency_type: DependencyType,
):
    config = get_or_initialize_config()
    dependencies = config.get_dependencies()

    typed_dependencies = [
        preprocess_requirement(dep)
        for dep in dependencies
        if classify_dependency(dep) == dependency_type
    ]

    to_delete = set()
    updated_packages = set()

    if dependency_type == DependencyType.PIP:
        for package_req in new_package_ids:
            for dep in typed_dependencies:
                dep_req = Requirement(dep)
                if dep_req.name == package_req.name:
                    to_delete.add(dep)
                    updated_packages.add(package_req.name)

            if package_req.name not in updated_packages:
                logger.info(f"Installed new package: {str(package_req)}")
            else:
                logger.info(f"Updated package: {str(package_req)}")
    else:  # GIT dependencies
        for package_dep in new_package_ids:
            for dep in typed_dependencies:
                dep_gh = GitHubDependency.from_string(dep)
                if dep_gh.org == package_dep.org and dep_gh.repo == package_dep.repo:
                    to_delete.add(dep)
                    updated_packages.add(package_dep.format_no_version())

            if f"{package_dep.org}/{package_dep.repo}" not in updated_packages:
                logger.info(f"Installed {str(package_dep)}")
            else:
                logger.info(f"Updated {str(package_dep)}")

    # Remove old versions of updated packages
    dependencies = [dep for dep in dependencies if dep not in to_delete]

    # Add new packages while preserving order
    new_deps = []
    # @dev Could be better here maybe
    for dep in dependencies + [str(package) for package in new_package_ids]:
        if dep not in new_deps:
            new_deps.append(dep)

    if len(new_deps) > 0:
        config.write_dependencies(new_deps)


def preprocess_requirement(package: str) -> str:
    package = package.strip().strip("'\"")
    git_url_pattern = r"^git\+https?://.*"
    if re.match(git_url_pattern, package):
        package_name = package.split("/")[-1].replace(".git", "")
        return package_name
    return package
