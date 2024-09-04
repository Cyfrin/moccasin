from gaboon.config import Config
from gaboon.constants.vars import DEPENDENCIES_FOLDER


# TODO: maybe move this to be a Config staticmethod
def get_base_install_path():
    project_root = Config.find_project_root()
    base_install_path = project_root / DEPENDENCIES_FOLDER
    base_install_path.mkdir(exist_ok=True)
    return base_install_path
