from argparse import Namespace
import subprocess
from packaging.requirements import Requirement
from gaboon.config import get_config
from gaboon._dependency_helpers import get_base_install_path
from gaboon.logging import logger


def main(args: Namespace):
    requirements = args.requirements
    if len(requirements) == 0:
        requirements = get_config().get_dependencies()
    _pip_install(requirements, args.quiet)


def _pip_install(package_ids: list[str], quiet: bool = False):
    path = get_base_install_path()
    for i in range(len(package_ids)):
        if "/" in package_ids[i]:
            package_ids[i] = (
                package_ids[i].split("/")[-1]
                + " @ git+https://github.com/"
                + package_ids[i]
            )

    # TODO: Allow for multiple versions of the same package to be installed
    cmd = ["uv", "pip", "install", *package_ids, "--target", str(path)]

    # TODO: `--upgrade` and `--force` options.
    capture_output = quiet
    subprocess.run(cmd, capture_output=capture_output, check=True)

    config = get_config()
    dependencies = config.get_dependencies()

    to_delete = set()
    for package in package_ids:
        for dep in dependencies:
            if Requirement(dep).name == Requirement(package).name:
                to_delete.add(dep)
        logger.info(f"Installed {package}")

    dependencies = [dep for dep in dependencies if dep not in to_delete]
    # TODO: keep original order of dependencies
    # e.g. if gaboon.toml has snekmate==0.1.0 and user installs
    # snekmate==0.2.0, we should keep the original order in the toml file.
    dependencies.extend(package_ids)

    config.write_dependencies(dependencies)
