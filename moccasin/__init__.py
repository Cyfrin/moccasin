import sys
from pathlib import Path

from moccasin import __main__


def main():
    __main__.main(sys.argv[1:])


def version() -> str:
    return __main__.get_version()


def setup_notebook(path: str | Path | None = None):
    from pathlib import Path

    from moccasin._sys_path_and_config_setup import (
        _set_sys_path,
        _setup_network_and_account_from_config_and_cli,
        get_sys_paths_list,
    )
    from moccasin.config import get_or_initialize_config

    normalized_path: Path = Path(path) if path is not None else Path.cwd()
    config = get_or_initialize_config(normalized_path)

    # Set up the environment (add necessary paths to sys.path, etc.)
    _set_sys_path(get_sys_paths_list(config))
    _setup_network_and_account_from_config_and_cli()


if __name__ == "__main__":
    main()
