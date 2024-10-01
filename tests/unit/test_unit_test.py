import os
from pathlib import Path

import pytest

from moccasin.commands.test import _run_project_tests
from moccasin.config import get_or_initialize_config
from tests.conftest import COMPLEX_PROJECT_PATH


def test_duplicate_fixtures(complex_conftest_override, capsys):
    current_dir = Path.cwd()
    try:
        os.chdir(current_dir.joinpath(COMPLEX_PROJECT_PATH))
        config = get_or_initialize_config()
        with pytest.raises(SystemExit) as exc_info:
            _run_project_tests([], config=config)
    finally:
        os.chdir(current_dir)

    assert exc_info.value.code == 4
    captured = capsys.readouterr()

    # Check for the error message in the output
    assert "DuplicateFixtureNameError" in captured.err
    assert "Duplicate fixture name 'eth_usd' found in tuples" in captured.err
    assert "('price_feed', 'eth_usd')" in captured.err
