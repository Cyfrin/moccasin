import argparse
from typing import Tuple

from moccasin.__main__ import generate_main_parser_and_sub_parsers


# ------------------------------------------------------------------
#                          CLI COMMANDS
# ------------------------------------------------------------------
# Wrapper function for sphinx-argparse
def get_main_parser() -> argparse.ArgumentParser:
    main_parser, _ = generate_main_parser_and_sub_parsers()
    return main_parser


def get_parsers() -> Tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]]:
    main_parser, subparsers_action = generate_main_parser_and_sub_parsers()
    subparsers = {
        choice: subparsers_action.choices[choice]  # type: ignore
        for choice in subparsers_action.choices  # type: ignore
    }
    return main_parser, subparsers


def get_subparser(name: str) -> argparse.ArgumentParser:
    _, subparsers = get_parsers()
    return subparsers[name]


def get_init():
    return get_subparser("init")


def get_compile():
    return get_subparser("compile")


def get_run():
    return get_subparser("run")


def get_deploy():
    return get_subparser("deploy")


def get_deployments():
    return get_subparser("deployments")


def get_install():
    return get_subparser("install")


def get_test():
    return get_subparser("test")


def get_wallet():
    return get_subparser("wallet")


def get_console():
    return get_subparser("console")


def get_purge():
    return get_subparser("purge")


def get_config():
    return get_subparser("config")


def get_explorer():
    return get_subparser("explorer")


def get_inspect():
    return get_subparser("inspect")
