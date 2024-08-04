# Much of this was inspired by https://github.com/eth-brownie/brownie/tree/master
from argparse import Namespace
import os
import tomli_w
import re
from gaboon.config import Config, get_config, initialize_global_config
from gaboon.constants.vars import (
    REQUEST_HEADERS,
    PACKAGE_VERSION_FILE,
    DEPENDENCIES_FOLDER,
)
from base64 import b64encode
import requests
from tqdm import tqdm
import shutil
import zipfile
from io import BytesIO
from gaboon.logging import logger
from urllib.parse import quote
import tomllib


def main(args: Namespace) -> int:
    if args.github_repo is None:
        _install_dependencies()
    else:
        _install_from_github(args.github_repo)
    return 0


def _install_dependencies():
    config = get_config()
    if config is None:
        initialize_global_config()
        config = get_config()
    dependencies = config.get_dependencies()
    for package_name in dependencies:
        package_id = f"{package_name}@{dependencies[package_name]}"
        _install_from_github(package_id)


def _install_from_github(package_id: str) -> str:
    version = None
    try:
        path, version = package_id.split("@", 1)
    except ValueError:
        logger.info("Version not provided. Will attempt to install latest version.")
        path = package_id
    try:
        org, repo = path.split("/")
    except ValueError:
        raise ValueError(
            "Invalid package ID. Must be given as [ORG]/[REPO]@[VERSION]"
            "\ne.g. 'OpenZeppelin/openzeppelin-contracts@v2.5.0'"
        ) from None
    if not version:
        url = f"https://api.github.com/repos/{org}/{repo}/releases/latest"
        version = (requests.get(url)).json()["tag_name"].lstrip("v")
        logger.debug(f"Latest version of {package_id} is {version}.")
    if not version:
        raise ValueError(
            "Invalid package ID, could not find latest version. Must be given as [ORG]/[REPO]@[VERSION]"
            "\ne.g. 'OpenZeppelin/openzeppelin-contracts@v2.5.0'"
        ) from None

    project_root = Config.find_project_root()
    base_install_path = project_root.joinpath(DEPENDENCIES_FOLDER)
    base_install_path.mkdir(exist_ok=True)
    org_install_path = base_install_path.joinpath(f"{org}")
    org_install_path.mkdir(exist_ok=True)
    install_path = org_install_path.joinpath(f"{repo}")
    versions_install_path = base_install_path.joinpath(PACKAGE_VERSION_FILE)

    # TODO: Allow for multiple versions of the same package to be installed
    if install_path.exists():
        with open(versions_install_path, "rb") as f:
            versions = tomllib.load(f)
            installed_version = versions.get(f"{org}/{repo}", None)
        if installed_version == version:
            logger.info(f"{org}/{repo}@{version} already installed")
            return f"{org}/{repo}@{version}"
        else:
            logger.info(f"Updating {org}/{repo} from {installed_version} to {version}")

    headers = REQUEST_HEADERS.copy()
    headers.update(_maybe_retrieve_github_auth())

    if re.match(r"^[0-9a-f]+$", version):
        download_url = f"https://api.github.com/repos/{org}/{repo}/zipball/{version}"
    else:
        download_url = _get_download_url_from_tag(org, repo, version, headers)
    existing = list(install_path.parent.iterdir())

    # Some versions contain special characters and github api seems to display url without
    # encoding them.
    # It results in a ConnectionError exception because the actual download url is encoded.
    # In this case we try to sanitize the version in url and download again.
    try:
        _stream_download(download_url, str(install_path.parent), headers)
    except ConnectionError:
        download_url = f"https://api.github.com/repos/{org}/{repo}/zipball/refs/tags/{quote(version)}"
        _stream_download(download_url, str(install_path.parent), headers)

    installed = next(i for i in install_path.parent.iterdir() if i not in existing)
    shutil.move(installed, install_path)

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

    logger.info(f"Installed {package_id}")

    _add_package_to_config(org, repo, version)

    return f"{org}/{repo}@{version}"


def _add_package_to_config(org: str, repo: str, version: str) -> None:
    config = get_config()
    if config is None:
        initialize_global_config()
        config = get_config()
    dependencies = config.get_dependencies()
    if f"{org}/{repo}" not in dependencies:
        logger.debug(f"Adding {org}/{repo}@{version} to dependencies")
        dependencies[f"{org}/{repo}"] = version
        config.write_dependencies(dependencies)


def _maybe_retrieve_github_auth() -> dict[str, str]:
    """Returns appropriate github authorization headers.

    Otherwise returns an empty dict if no auth token is present.
    """
    token = os.getenv("GITHUB_TOKEN")
    if token:
        auth = b64encode(token.encode()).decode()
        return {"Authorization": f"Basic {auth}"}
    return {}


def _get_download_url_from_tag(org: str, repo: str, version: str, headers: dict) -> str:
    response = requests.get(
        f"https://api.github.com/repos/{org}/{repo}/tags?per_page=100", headers=headers
    )
    if response.status_code != 200:
        msg = "Status {} when getting package versions from Github: '{}'".format(
            response.status_code, response.json()["message"]
        )
        if response.status_code in (403, 404):
            msg += (
                "\n\nMissing or forbidden.\n"
                "If this issue persists, generate a Github API token and store"
                " it as the environment variable `GITHUB_TOKEN`:\n"
                "https://github.blog/2013-05-16-personal-api-tokens/"
            )
        raise ConnectionError(msg)

    data = response.json()
    if not data:
        raise ValueError("Github repository has no tags set")
    org, repo = data[0]["zipball_url"].split("/")[3:5]
    tags = [i["name"].lstrip("v") for i in data]
    if version not in tags:
        raise ValueError(
            "Invalid version for this package. Available versions are:\n"
            + ", ".join(tags)
        ) from None

    return next(i["zipball_url"] for i in data if i["name"].lstrip("v") == version)


def _stream_download(
    download_url: str, target_path: str, headers: dict[str, str] = REQUEST_HEADERS
) -> None:
    response = requests.get(download_url, stream=True, headers=headers)

    if response.status_code == 404:
        raise ConnectionError(
            f"404 error when attempting to download from {download_url} - "
            "are you sure this is a valid mix? https://github.com/brownie-mix"
        )
    if response.status_code != 200:
        raise ConnectionError(
            f"Received status code {response.status_code} when attempting "
            f"to download from {download_url}"
        )

    total_size = int(response.headers.get("content-length", 0))
    progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)
    content = bytes()

    for data in response.iter_content(1024, decode_unicode=True):
        progress_bar.update(len(data))
        content += data
    progress_bar.close()

    with zipfile.ZipFile(BytesIO(content)) as zf:
        zf.extractall(target_path)
