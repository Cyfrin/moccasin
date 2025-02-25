import tomllib
from pathlib import Path

import tomli_w

from tests.constants import LIB_GH_PATH, MOCCASIN_TOML, VERSIONS_TOML


def rewrite_temp_moccasin_toml_dependencies(
    temp_path: Path, dependencies: list[str] | None
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
    if dependencies is None or len(dependencies) == 0:
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


def get_temp_versions_toml_gh(temp_path: Path) -> dict:
    """Get the versions (github) from their lib/github toml file

    :param temp_path: Path to the temporary directory containing the moccasin.toml file.
    :type temp_path: Path
    :return: A dictionary containing the versions of the libraries.
    :rtype: dict
    """
    github_versions = {}

    # Github versions
    if temp_path.joinpath(f"{LIB_GH_PATH}/{VERSIONS_TOML}").exists():
        with open(temp_path.joinpath(f"{LIB_GH_PATH}/{VERSIONS_TOML}"), "rb") as f:
            versions = tomllib.load(f)
            github_versions = {k.lower(): v for k, v in versions.items()}

    return github_versions
