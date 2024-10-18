from argparse import Namespace

from moccasin.config import Config, get_config
from moccasin.logging import logger


def main(args: Namespace):
    config: Config = get_config()
    configuration_file = config.read_configs()
    logger.info(toml_like_pretty_print(configuration_file))
    return 0


def toml_like_pretty_print(data, indent=0):
    result = []
    for key, value in data.items():
        if isinstance(value, dict):
            result.append(f"{'  ' * indent}[{key}]")
            result.append(toml_like_pretty_print(value, indent + 1))
        elif isinstance(value, list):
            result.append(f"{'  ' * indent}{key} = [")
            for item in value:
                result.append(f"{'  ' * (indent + 1)}{repr(item)},")
            result.append(f"{'  ' * indent}]")
        else:
            result.append(f"{'  ' * indent}{key} = {repr(value)}")
    return "\n".join(result)
