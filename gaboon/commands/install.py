# Much of this was inspired by https://github.com/eth-brownie/brownie/tree/master
from argparse import Namespace
import os
import subprocess
import re
from gaboon.config import Config
from gaboon.constants.vars import REQUEST_HEADERS
from base64 import b64encode
import requests
from tqdm import tqdm
import shutil
import zipfile
from io import BytesIO

INSTALL_PATH = "lib"

def main(args: Namespace) -> int:
    # TODO: Need to add a conditional, where if no github org is provided, do the following:
    # 1. Check the toml for a list of packages
    # 2. Loop through each list and check if the package is downloaded already
    # 3. If not, download the package from the package registry
    _install_from_github(args.github_repo)
    return 0


def _install_from_github(package_id: str) -> str:
    try:
        path, version = package_id.split("@", 1)
        org, repo = path.split("/")
    except ValueError:
        raise ValueError(
            "Invalid package ID. Must be given as [ORG]/[REPO]@[VERSION]"
            "\ne.g. 'OpenZeppelin/openzeppelin-contracts@v2.5.0'"
        ) from None

    project_root = Config.find_project_root()
    base_install_path = project_root.joinpath(INSTALL_PATH)
    base_install_path.mkdir(exist_ok=True)
    install_path = base_install_path.joinpath(f"{org}")
    install_path.mkdir(exist_ok=True)
    install_path = install_path.joinpath(f"{repo}@{version}")
    if install_path.exists():
        raise FileExistsError("Package is aleady installed")

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

    # This is where you automatically add the dependency to the gaboon.toml, it should be updated
    # try:
    #     if not install_path.joinpath("brownie-config.yaml").exists():
    #         brownie_config: dict = {"project_structure": {}}

    #         contract_paths = set(
    #             i.relative_to(install_path).parts[0]
    #             for i in install_path.glob("**/*.sol")
    #         )
    #         contract_paths.update(
    #             i.relative_to(install_path).parts[0]
    #             for i in install_path.glob("**/*.vy")
    #         )
    #         if not contract_paths:
    #             raise ValueError(f"{package_id} does not contain any .sol or .vy files")
    #         if install_path.joinpath("contracts").is_dir():
    #             brownie_config["project_structure"]["contracts"] = "contracts"
    #         elif len(contract_paths) == 1:
    #             brownie_config["project_structure"]["contracts"] = contract_paths.pop()
    #         else:
    #             raise Exception(
    #                 f"{package_id} has no `contracts/` subdirectory, and "
    #                 "multiple directories containing source files"
    #             )

    #         with install_path.joinpath("brownie-config.yaml").open("w") as fp:
    #             yaml.dump(brownie_config, fp)

    #         Path.touch(install_path / ".env")

    #     project = load(install_path)
    #     project.close()
    # except InvalidPackage:
    #     shutil.rmtree(install_path)
    #     raise
    # except Exception as e:
    #     notify(
    #         "WARNING",
    #         f"Unable to compile {package_id} due to a {type(e).__name__} - you may still be able to"
    #         " import sources from the package, but will be unable to load the package directly.\n",
    #     )

    return f"{org}/{repo}@{version}"


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
