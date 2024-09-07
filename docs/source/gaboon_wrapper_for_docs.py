from gaboon.__main__ import generate_main_parser_and_sub_parsers
import argparse


# Wrapper function for sphinx-argparse
def get_main_parser() -> argparse.ArgumentParser:
    main_parser, _ = generate_main_parser_and_sub_parsers()
    return main_parser
