from pathlib import Path

# File Names
CONFIG_NAME = "gaboon.toml"
README_PATH = "README.md"
COUNTER_CONTRACT = "Counter.vy"

# Folder Names
BUILD_FOLDER = "out"
CONTRACTS_FOLDER = "src"
TESTS_FOLDER = "tests"
SCRIPT_FOLDER = "script"

# Complex Vars
PROJECT_FOLDERS = [CONTRACTS_FOLDER, TESTS_FOLDER, SCRIPT_FOLDER]

DEFAULT_KEYSTORES_PATH = Path.home().joinpath(".gaboon/keystores")
# TODO - add a --foundry flag for wallet commands to use foundry keystores
FOUNDRTY_KEYSTORES_PATH = Path.home().joinpath(".foundry/keystores")
