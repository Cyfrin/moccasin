import sys

from moccasin import __main__


def main():
    __main__.main(sys.argv[1:])


def version() -> str:
    return __main__.get_version()


def setup_notebook():
    from moccasin.config import initialize_global_config
    from moccasin._sys_path_and_config_setup import (
        _set_sys_path,
        get_sys_paths_list,
        _setup_network_and_account_from_config_and_cli,
    )

    config = initialize_global_config()

    # Set up the environment (add necessary paths to sys.path, etc.)
    _set_sys_path(get_sys_paths_list(config))
    _setup_network_and_account_from_config_and_cli()


if __name__ == "__main__":
    main()
