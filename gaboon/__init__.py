import sys
from gaboon import __main__
from gaboon.config import Config

# TODO - move this into __init__.py of gaboon folder so we can do better shit
_config: Config = None


def get_config() -> Config:
    global _config
    return _config


def initialize_global_config():
    global _config
    assert _config is None
    _config = Config.load_config_from_path()


def main():
    __main__.main(sys.argv[1:])


if __name__ == "__main__":
    main()
