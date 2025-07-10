import sys
from pathlib import Path
import cProfile
import pstats
import io

from moccasin import __main__


def main():
    argv = sys.argv[1:]
    # Check for either --profile or -p
    # @dev testing functionality
    if any(flag in argv for flag in ("--profile", "-p")):
        argv = [arg for arg in argv if arg not in ("--profile", "-p")]
        # Run cProfile for the main function
        pr = cProfile.Profile()
        pr.enable()
        exit_code = __main__.main(argv)
        pr.disable()
        # Store the profiling results
        # @dev might changed in the future
        profile_path = "moccasin_profile.prof"
        pr.dump_stats(profile_path)
        print(f"\n[Profiling] Raw cProfile stats saved to {profile_path}.\n" \
              f"You can analyze it with 'uv run snakeviz {profile_path}', 'uv run -m pstats {profile_path}', or similar tools.")
        sys.exit(exit_code)
    __main__.main(argv)


def version() -> str:#
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
