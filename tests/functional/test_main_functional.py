import tempfile
from pathlib import Path
import subprocess
from tests.base_test import assert_files_and_folders_exist
import pytest
from gaboon.cli.__main__ import __doc__ as doc

# This will skip all the tests in here.
pytestmark = pytest.mark.subprocess


def test_help():
    result = subprocess.run(
        ["gab", "-h"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout in doc, "Help output does not contain expected text"


def test_init():
    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(
            ["gab", "init", Path(temp_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        assert_files_and_folders_exist(Path(temp_dir))
