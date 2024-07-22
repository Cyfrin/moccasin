import subprocess
import tempfile
from pathlib import Path
from gaboon.project.project_class import Project

import pytest
from tests.base_test import assert_files_and_folders_exist

EXPECTED_HELP_TEXT = "Pythonic Smart Contract Development Framework"

# This will skip all the tests in here.
pytestmark = pytest.mark.subprocess


def test_help():
    result = subprocess.run(
        ["gab", "-h"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert (
        EXPECTED_HELP_TEXT in result.stdout
    ), "Help output does not contain expected text"


def test_init():
    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(
            ["gab", "init", Path(temp_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        assert_files_and_folders_exist(Path(temp_dir))
        assert_files_and_folders_exist(Path(temp_dir))


def test_find_project_root_from_new_project():
    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(
            ["gab", "init", Path(temp_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        project_root: Path = Project.find_project_root(Path(temp_dir))
        assert project_root.resolve() == Path(temp_dir).resolve()
