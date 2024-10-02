import re
from dataclasses import dataclass
from enum import Enum

from packaging.requirements import InvalidRequirement, Requirement

from moccasin.config import get_or_initialize_config
from moccasin.logging import logger


class DependencyType(Enum):
    GITHUB = "github"
    PIP = "pip"


def classify_dependency(dependency: str) -> DependencyType:
    dependency = dependency.strip().strip("'\"")

    github_shorthand = r"^([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)(@[a-zA-Z0-9_.-]+)?$"
    github_url = r"^https://github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$"

    if re.match(github_shorthand, dependency) or re.match(github_url, dependency):
        return DependencyType.GITHUB

    return DependencyType.PIP


def _write_new_dependencies(
    new_package_ids: list[str], dependency_type: DependencyType
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
        for package in new_package_ids:
            try:
                processed_package = preprocess_requirement(package)
                package_req = Requirement(processed_package)
            except InvalidRequirement:
                logger.warning(f"Invalid requirement format for package: {package}")
                continue
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
                    updated_packages.add(package_dep.format_no_version())

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

    if len(new_deps) > 0:
        config.write_dependencies(new_deps)


def preprocess_requirement(package: str) -> str:
    package = package.strip().strip("'\"")
    git_url_pattern = r"^git\+https?://.*"
    if re.match(git_url_pattern, package):
        package_name = package.split("/")[-1].replace(".git", "")
        return package_name
    return package


@dataclass
class GitHubDependency:
    org: str
    repo: str
    version: str | None = None

    @classmethod
    def from_string(cls, dep_string: str) -> "GitHubDependency":
        if "@" in dep_string:
            path, version = dep_string.split("@")
        else:
            path, version = dep_string, None

        org, repo = str(path).split("/")
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
