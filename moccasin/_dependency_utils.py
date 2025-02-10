import os
import re
import tomllib
from base64 import b64encode
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Tuple

import requests  # type: ignore
import tomli_w
from packaging.requirements import InvalidRequirement, Requirement, SpecifierSet

from moccasin.config import get_or_initialize_config
from moccasin.constants.vars import GITHUB, PACKAGE_VERSION_FILE, PYPI, REQUEST_HEADERS
from moccasin.logging import logger


class DependencyType(Enum):
    """Enumeration of supported dependency types.

    .. attribute:: GITHUB
        Dependencies from GitHub repositories (format: 'owner/repo[@version]' or GitHub URL)

    .. attribute:: PIP
        Dependencies from PyPI (Python Package Index)
    """

    GITHUB = "github"
    PIP = "pip"


# ------------------------------------------------------------------
#                       HANDLE DEPENDENCIES
# ------------------------------------------------------------------
def classify_dependency(dependency: str) -> DependencyType:
    """Classify a dependency string as either a GitHub or PyPI dependency.

    :param dependency: The dependency string to classify
    :type dependency: str
    :return: GITHUB if the dependency matches GitHub patterns, PIP otherwise
    :rtype: DependencyType

    The dependency string can be in the following formats:
        * PyPI: ``package_name[==version]``
        * GitHub: ``owner/repo[@version]`` or ``https://github.com/owner/repo``

    Example:
        >>> classify_dependency("numpy>=1.20.0")
        DependencyType.PIP
        >>> classify_dependency("owner/repo@v1.0.0")
        DependencyType.GITHUB
    """
    dependency = dependency.strip().strip("'\"")

    github_shorthand = r"^([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)(@[a-zA-Z0-9_.-]+)?$"
    github_url = r"^https://github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$"

    if re.match(github_shorthand, dependency) or re.match(github_url, dependency):
        return DependencyType.GITHUB

    return DependencyType.PIP


def get_new_or_updated_dependencies(
    requirements: list[str], config_dependencies: list[str], base_install_path: Path
) -> Tuple[list["PipDependency"], list["GitHubDependency"]]:
    """Return a tuple with the pip and github dependencies.

    If no requirements are given, return empty lists for both dependencies.

    :param requirements: List of requirements to parse
    :type requirements: list[str]
    :param config_dependencies: List of dependencies from mox config
    :type config_dependencies: list[str]
    :param base_install_path: Path to the base install path
    :type base_install_path: Path
    :return: Tuple with the pip and github dependencies
    :rtype: Tuple[list["PipDependency"], list["GitHubDependency"]]
    """

    # Get pip and github paths
    pip_install_path = base_install_path.joinpath(PYPI)
    github_install_path = base_install_path.joinpath(GITHUB)

    # Get versions toml files
    pip_versions_toml = _get_install_path_versions_toml(pip_install_path)
    github_versions_toml = _get_install_path_versions_toml(github_install_path)

    # Init dependencies lists
    pip_new_or_updated: list["PipDependency"] = []
    github_new_or_updated: list["GitHubDependency"] = []
    project_requirements = config_dependencies + requirements

    # # Check if we have any requirements to parse
    if len(project_requirements) == 0:
        # If we have no requirements, return dict with empty lists
        return (pip_new_or_updated, github_new_or_updated)

    # Populate requirements lists
    for package in project_requirements:
        if classify_dependency(package) == DependencyType.PIP:
            pip_req = _get_new_or_updated_pip_dependency(package, pip_versions_toml)
            if pip_req is not None:
                pip_new_or_updated.append(pip_req)
        else:
            github_req = _get_new_or_updated_github_dependency(
                package, github_versions_toml
            )
            if github_req is not None:
                github_new_or_updated.append(github_req)

    return (pip_new_or_updated, github_new_or_updated)


def _get_install_path_versions_toml(lib_install_path: Path) -> dict[str, str]:
    """Read and return the versions from a TOML file in the installation path.

    :param lib_install_path: Path to the library installation directory
    :type lib_install_path: Path
    :return: Dictionary mapping package names (lowercase) to their versions
    :rtype: dict[str, str]

    :note: Returns empty dict if versions file doesn't exist
    """
    versions_toml: dict[str, str] = {}
    versions_install_path = lib_install_path.joinpath(PACKAGE_VERSION_FILE)
    if not versions_install_path.exists():
        return versions_toml

    # If versions file exists, load and normalize package names to lowercase
    with open(versions_install_path, "rb") as f:
        versions = tomllib.load(f)
        versions_toml = {k.lower(): v for k, v in versions.items()}

    return versions_toml


# ------------------------------------------------------------------
#                         PIP DEPENDENCIES
# ------------------------------------------------------------------
@dataclass
class PipDependency:
    """Helper class for managing PyPI dependencies.

    :ivar requirement: Parsed package requirement (name and version specifiers)
    :type requirement: Requirement
    :ivar no_version: Flag indicating if original requirement had no version specified
    :type no_version: bool
    """

    requirement: Requirement
    no_version: bool = False

    def __str__(self) -> str:
        return str(self.requirement)


def _get_new_or_updated_pip_dependency(
    package: str, pip_versions_toml: dict[str, str]
) -> PipDependency | None:
    """Process a pip package and determine if it needs to be installed or updated.

    :param package: Package specification (e.g., "numpy>=1.20.0")
    :type package: str
    :param pip_versions_toml: Current installed versions from versions.toml
    :type pip_versions_toml: dict[str, str]
    :return: A PipDependency instance if package needs installation/update, None if current version satisfies requirements
    :rtype: PipDependency | None
    :raises InvalidRequirement: If package string is not a valid pip requirement
    :raises ValueError: If unable to determine latest version from PyPI

    This function handles several cases:
        1. New packages not in versions.toml
        2. Existing packages that need version updates
        3. Packages with no version specified (uses latest from PyPI)
    """
    no_version = False
    # Try to parse the package as a pip requirement
    try:
        # Preprocess package name
        processed_package = preprocess_requirement(package)
        package_req = Requirement(processed_package)
        if package_req.specifier is None:
            no_version = True
            package_req.specifier = SpecifierSet(
                f"=={_get_latest_pip_version(package_req.name)}"
            )
    except InvalidRequirement:
        logger.warning(f"Invalid requirement format for package: {package}")
        return None

    # If no version toml file, add new package
    if not bool(pip_versions_toml):
        return PipDependency(requirement=package_req, no_version=no_version)

    # Get installed version
    installed_version = SpecifierSet(pip_versions_toml.get(package_req.name.lower()))
    if installed_version is None:
        installed_version = SpecifierSet(
            f"=={_get_latest_pip_version(package_req.name)}"
        )
        logger.info(
            f"Using latest version for {package_req.name}: {str(installed_version)}"
        )

    # If version number match requirement, package doesn't need to be updated
    if installed_version == package_req.specifier:
        logger.info(
            f"Package {package_req.name} is already installed at version {installed_version}"
        )
        return None

    # If version number doesn't match requirement, package needs to be updated
    logger.info(f"Package {package_req.name} needs to be updated")
    return PipDependency(requirement=package_req, no_version=no_version)


def _get_latest_pip_version(package_name: str) -> str:
    """Fetch the latest version of a package from PyPI.

    :param package_name: Name of the package
    :type package_name: str
    :return: Latest version of the package
    :rtype: str
    :raises ValueError: If unable to determine latest version
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["info"]["version"]

    raise ValueError(f"Unable to determine latest version for {package_name}")


# ------------------------------------------------------------------
#                         GH DEPENDENCIES
# ------------------------------------------------------------------
@dataclass
class GitHubDependency:
    """Helper class for managing GitHub dependencies.

    :ivar org: GitHub organization/owner name
    :type org: str
    :ivar repo: Repository name
    :type repo: str
    :ivar version: Version tag/branch/commit (optional)
    :type version: str | None
    :ivar headers: GitHub API request headers (for authentication)
    :type headers: dict | None
    :ivar no_version: Flag indicating if original requirement had no version
    :type no_version: bool

    The dependency can be specified in formats:
        * ``owner/repo[@version]``
        * ``https://github.com/owner/repo[@version]``
    """

    org: str
    repo: str
    version: str | None = None
    headers: dict | None = None
    no_version: bool = False

    @classmethod
    def from_string(cls, dep_string: str) -> "GitHubDependency":
        """Create a GitHubDependency instance from a string.

        :param dep_string: Dependency string in the format 'owner/repo[@version]'
        :type dep_string: str
        :return: GitHubDependency instance
        :rtype: GitHubDependency
        :raises ValueError: If invalid dependency string
        """
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
        # @dev GitHub repository URLs are case-insensitive
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


def _get_new_or_updated_github_dependency(
    package: str, github_versions_toml: dict[str, str]
) -> GitHubDependency | None:
    """Process a GitHub dependency and determine if it needs to be installed or updated.

    :param package: Package specification (e.g., "owner/repo@v1.0.0")
    :type package: str
    :param github_versions_toml: Current installed versions from versions.toml
    :type github_versions_toml: dict[str, str]
    :return: A GitHubDependency instance if package needs installation/update, None if current version satisfies requirements
    :rtype: GitHubDependency | None
    """
    github_dependency = GitHubDependency.from_string(package)

    headers = REQUEST_HEADERS.copy()
    headers.update(_maybe_retrieve_github_auth())

    if github_dependency.headers is None:
        github_dependency.headers = headers

    if github_dependency.version is None:
        github_dependency.no_version = True
        github_dependency.version = _get_latest_github_version(
            github_dependency.org, github_dependency.repo, github_dependency.headers
        )
        logger.info(
            f"Using latest version for {github_dependency.org}/{github_dependency.repo}: {github_dependency.version}"
        )

    if not bool(github_versions_toml):
        return github_dependency

    installed_version = github_versions_toml.get(
        f"{github_dependency.org}/{github_dependency.repo}", None
    )

    if installed_version is None:
        installed_version = _get_latest_github_version(
            github_dependency.org, github_dependency.repo, github_dependency.headers
        )
        logger.info(
            f"Using latest version for {github_dependency.org}/{github_dependency.repo}: {installed_version}"
        )

    if installed_version == github_dependency.version:
        logger.info(
            f"{github_dependency.org}/{github_dependency.repo} already installed at version {github_dependency.version}"
        )
        return None

    logger.info(
        f"{github_dependency.org}/{github_dependency.repo} needs to be updated from version {installed_version} to {github_dependency.version}"
    )
    return github_dependency


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
    """Fetch the latest release version from a GitHub repository.

    :param org: GitHub organization/owner name
    :type org: str
    :param repo: Repository name
    :type repo: str
    :param headers: GitHub API request headers (for authentication)
    :type headers: dict
    :return: Latest release version tag
    :rtype: str
    :raises ValueError: If unable to fetch or determine latest version
    """
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
    versions_install_path: Path, dependency: GitHubDependency | PipDependency
):
    """Update the versions file with a new or updated dependency.

    :param versions_install_path: Path to the versions file
    :type versions_install_path: Path
    :param dependency: Dependency to add or update
    :type dependency: GitHubDependency | PipDependency
    """
    # Update versions file
    if versions_install_path.exists():
        with open(versions_install_path, "rb") as f:
            versions_data = tomllib.load(f)
        if isinstance(dependency, GitHubDependency):
            versions_data[f"{dependency.org}/{dependency.repo}"] = dependency.version
        else:
            versions_data[f"{dependency.requirement.name.lower()}"] = str(
                dependency.requirement.specifier
            )

        with open(versions_install_path, "wb") as f:
            tomli_w.dump(versions_data, f)
    else:
        with open(versions_install_path, "w", encoding="utf-8") as f:
            if isinstance(dependency, GitHubDependency):
                toml_string = tomli_w.dumps(
                    {f"{dependency.org}/{dependency.repo}": dependency.version}
                )
            else:
                toml_string = tomli_w.dumps(
                    {
                        dependency.requirement.name.lower(): str(
                            dependency.requirement.specifier
                        )
                    }
                )
            f.write(toml_string)


def write_new_config_dependencies(
    new_packages: list[GitHubDependency | PipDependency],
    dependency_type: DependencyType,
):
    """Update the configuration with new or updated dependencies.

    :param new_packages: List of new or updated dependencies
    :type new_packages: list[GitHubDependency | PipDependency]
    :param dependency_type: Type of dependencies (GitHub or PyPI)
    :type dependency_type: DependencyType
    """
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
        for pip_dependency in new_packages:
            for dep in typed_dependencies:
                dep_req = Requirement(dep)
                if dep_req.name.lower() == pip_dependency.requirement.name.lower():
                    to_delete.add(dep)
                    updated_packages.add(pip_dependency.requirement.name)

            if pip_dependency.requirement.name not in updated_packages:
                logger.info(
                    f"Installed new package: {str(pip_dependency.requirement.name.lower())}"
                )
            else:
                logger.info(
                    f"Updated package: {str(pip_dependency.requirement.name.lower())}"
                )
    else:  # GIT dependencies
        for package_dep in new_packages:
            for dep in typed_dependencies:
                dep_gh = GitHubDependency.from_string(dep)
                if dep_gh.org == package_dep.org and dep_gh.repo == package_dep.repo:
                    to_delete.add(dep)
                    updated_packages.add(package_dep.format_no_version())

            if f"{package_dep.org}/{package_dep.repo}" not in updated_packages:
                logger.info(f"Installed {str(package_dep.format_no_version())}")
            else:
                logger.info(f"Updated {str(package_dep.format_no_version())}")

    # Remove old versions of updated packages
    dependencies = [dep for dep in dependencies if dep not in to_delete]

    # Get new packgages name and version if not latest
    formated_new_packages: list[str] = []
    for package in new_packages:
        if package.no_version:
            if dependency_type == DependencyType.PIP:
                formated_new_packages.append(package.requirement.name)
            else:
                formated_new_packages.append(package.format_no_version())
        else:
            formated_new_packages.append(str(package))

    # Add new packages while preserving order
    new_deps = []
    for dep in dependencies + formated_new_packages:
        if dep not in new_deps:
            new_deps.append(dep)

    if len(new_deps) > 0:
        config.write_dependencies(new_deps)


def preprocess_requirement(package: str) -> str:
    """Preprocess a package string to remove any unnecessary characters.

    :param package: Package string
    :type package: str
    :return: Preprocessed package string
    :rtype: str
    """
    package = package.strip().strip("'\"")
    git_url_pattern = r"^git\+https?://.*"
    if re.match(git_url_pattern, package):
        package_name = package.split("/")[-1].replace(".git", "")
        return package_name
    return package
