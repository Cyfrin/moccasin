import shutil
import subprocess
import tempfile
import tomllib
from argparse import Namespace
from pathlib import Path

import tomli_w
from packaging.requirements import Requirement

from moccasin._dependency_utils import (
    DependencyType,
    GitHubDependency,
    classify_dependency,
    preprocess_requirement,
)
from moccasin.config import Config, get_or_initialize_config
from moccasin.constants.vars import GITHUB, PACKAGE_VERSION_FILE, PYPI
from moccasin.logging import logger, set_log_level


def main(args: Namespace):
    _purge(args.packages, args.quiet)


def _purge(packages: list[str], quiet: bool = False, config: Config = None):
    set_log_level(quiet)

    if config is None:
        config = get_or_initialize_config()

    pip_dependencies = []
    github_dependencies = []

    for package in packages:
        dep_type = classify_dependency(package)
        if dep_type == DependencyType.PIP:
            pip_dependencies.append(package)
        elif dep_type == DependencyType.GITHUB:
            github_dependencies.append(package)
        else:
            logger.error(f"Unknown dependency type for {package}")

    if len(pip_dependencies) > 0:
        _uninstall_pip_dependencies(pip_dependencies, config, quiet)

    if len(github_dependencies) > 0:
        _uninstall_github_dependencies(github_dependencies, config, quiet)


def _uninstall_pip_dependencies(
    packages: list[str], config: Config, quiet: bool = False
):
    path = config.get_root().joinpath(config.lib_folder).joinpath(PYPI)

    cmd = ["uv", "pip", "uninstall", *packages, "--target", str(path)]

    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True
    )
    if len(result.stdout.strip()) > 0:
        logger.info(result.stdout.strip())
    if len(result.stderr.strip()) > 0:
        logger.info(result.stderr.strip())

    if "No packages to uninstall" in result.stderr:
        logger.info(
            "Maybe you meant to format this as a GitHub dependency? Format: ORG/REPO[@VERSION]"
        )
        return

    config = get_or_initialize_config()
    dependencies = config.get_dependencies()

    dependency_type = DependencyType.PIP

    typed_dependencies = [
        preprocess_requirement(dep)
        for dep in dependencies
        if classify_dependency(dep) == dependency_type
    ]

    to_delete = set()
    for package in packages:
        for dep in typed_dependencies:
            if Requirement(dep).name == Requirement(package).name:
                to_delete.add(dep)
        logger.info(f"Removed {package}")

    dependencies = [dep for dep in dependencies if dep not in to_delete]
    config.write_dependencies(dependencies)


def _uninstall_github_dependencies(
    packages: list[str], config: Config, quiet: bool = False
):
    uninstall_path = config.get_root().joinpath(config.lib_folder).joinpath(GITHUB)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        if uninstall_path.exists():
            shutil.copytree(uninstall_path, temp_path, dirs_exist_ok=True)
        else:
            temp_path.mkdir(parents=True, exist_ok=True)
        versions_temp_path = temp_path.joinpath(PACKAGE_VERSION_FILE)
        versions_data = {}

        if versions_temp_path.exists():
            with open(versions_temp_path, "rb") as f:
                versions_data = tomllib.load(f)
                versions_data = {k.lower(): v for k, v in versions_data.items()}

        else:
            logger.warning("No versions file found. Continuing anyways.")

        total_packages = 0
        try:
            for package_id in packages:
                try:
                    if "@" in package_id:
                        path, _ = package_id.split("@", 1)
                    else:
                        path = package_id
                    org, repo = path.split("/")
                    org = org.strip().lower()
                    repo = repo.strip().lower()
                except ValueError:
                    raise ValueError(
                        "Invalid package ID. Must be given as ORG/REPO[@VERSION]"
                        "\ne.g. 'pcaversaccio/snekmate@v2.5.0'"
                    ) from None

                org_temp_path = temp_path.joinpath(f"{org}")
                repo_temp_path = org_temp_path.joinpath(f"{repo}")

                if not org_temp_path.exists() and not repo_temp_path.exists():
                    logger.warning(f"Package {org}/{repo} not found. Skipping.")
                    continue

                # Remove the package directory
                shutil.rmtree(repo_temp_path, ignore_errors=True)

                # Remove empty org directory if it exists
                if org_temp_path.exists() and not any(org_temp_path.iterdir()):
                    org_temp_path.rmdir()

                # Update versions data
                versions_data.pop(f"{org}/{repo}", None)
                total_packages += 1

            # Write updated versions file
            with open(versions_temp_path, "wb") as f:
                tomli_w.dump(versions_data, f)

            # If we've reached this point without exceptions, commit the changes
            if uninstall_path.exists():
                shutil.rmtree(uninstall_path)
            shutil.copytree(temp_path, uninstall_path, dirs_exist_ok=True)

        except Exception as e:
            logger.error(f"An error occurred during package removal: {str(e)}")
            raise

    if total_packages == 0:
        logger.info("No packages were found to uninstall.")
        return

    # REVIEW: We probably want to make this atomic as well, and write the depenedencies at the same time
    config = get_or_initialize_config()
    dependencies = config.get_dependencies()

    dependency_type = DependencyType.GITHUB

    typed_dependencies = [
        preprocess_requirement(dep)
        for dep in dependencies
        if classify_dependency(dep) == dependency_type
    ]

    to_delete = set()
    for package in packages:
        package_dep = GitHubDependency.from_string(package)
        for dep in typed_dependencies:
            dep_gh = GitHubDependency.from_string(dep)
            if dep_gh.org == package_dep.org and dep_gh.repo == package_dep.repo:
                to_delete.add(dep)
        logger.info(f"Removed {package}")

    dependencies = [dep for dep in dependencies if dep not in to_delete]
    config.write_dependencies(dependencies)
