from pathlib import Path
from typing import Any, List
from gaboon.config import initialize_global_config, get_config
from gaboon._add_sys_path import _add_to_sys_path
import pytest
import sys


# TODO
def main(pytest_args: List[Any]) -> int:
    initialize_global_config()
    return _run_project_tests(pytest_args)


def _run_project_tests(pytest_args: List[Any]) -> int:
    project_path: Path | None = get_config().get_root()
    _add_to_sys_path(project_path)
    return_code: int = pytest.main(["--assert=plain"] + pytest_args)
    if return_code:
        sys.exit(return_code)
