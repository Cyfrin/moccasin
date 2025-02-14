import tomllib
from pathlib import Path

import tomli_w

from tests.constants import (
    LIB_GH_PATH,
    LIB_PIP_PATH,
    MOCCASIN_TOML,
    NEW_VERSION,
    PATRICK_PACKAGE_NAME,
    PIP_PACKAGE_NAME,
    VERSIONS_TOML,
)


def rewrite_temp_moccasin_toml_dependencies(
    temp_path: Path,
    dependencies: list[str] = [
        f"{PIP_PACKAGE_NAME}=={NEW_VERSION}",
        f"{PATRICK_PACKAGE_NAME}",
    ],
) -> dict:
    """Rewrite the moccasin.toml file with new dependencies

    :param temp_path: Path to the temporary directory containing the moccasin.toml file.
    :type temp_path: Path
    :param dependencies: List of dependencies to add to the moccasin.toml file.
    :type dependencies: list[str]
    :return: Configuration data from the moccasin.toml file.
    :rtype: dict
    """
    if not temp_path.joinpath(MOCCASIN_TOML).exists():
        return {}

    # Read the moccasin.toml file
    with open(temp_path.joinpath(MOCCASIN_TOML), "rb") as f:
        old_moccasin_toml = tomllib.load(f)

    # Return if no dependencies are provided to keep the config
    if len(dependencies) == 0:
        return old_moccasin_toml

    with open(temp_path.joinpath(MOCCASIN_TOML), "wb") as f:
        # Update dependencies of moccasin.toml
        # @dev add new dependencies and keep config
        new_moccasin_toml = {
            **old_moccasin_toml,
            "project": {**old_moccasin_toml["project"], "dependencies": dependencies},
        }
        tomli_w.dump(new_moccasin_toml, f)

    return old_moccasin_toml


def get_temp_versions_toml_from_libs(temp_path: Path) -> tuple[dict, dict]:
    """Get the versions (github and pip) from their lib/github and lib/pypi toml files

    :param temp_path: Path to the temporary directory containing the moccasin.toml file.
    :type temp_path: Path
    :return: A tuple containing two dictionaries, each containing the versions of the libraries.
    :rtype: tuple[dict, dict]
    """
    github_versions = {}
    pip_versions = {}

    # Github versions
    if temp_path.joinpath(LIB_GH_PATH).exists():
        with open(temp_path.joinpath(LIB_GH_PATH).joinpath(VERSIONS_TOML), "rb") as f:
            versions = tomllib.load(f)
            github_versions = {k.lower(): v for k, v in versions.items()}

    # Pip versions
    if temp_path.joinpath(LIB_PIP_PATH).exists():
        with open(temp_path.joinpath(LIB_PIP_PATH).joinpath(VERSIONS_TOML), "rb") as f:
            versions = tomllib.load(f)
            pip_versions = {k.lower(): v for k, v in versions.items()}

    return github_versions, pip_versions
