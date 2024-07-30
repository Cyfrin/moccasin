from pathlib import Path
import pytest   
import os
import sys

COMPLEX_PROJECT_PATH = Path(__file__).parent.parent.joinpath(
    "data/complex_project/"
)

@pytest.fixture
def gab_path():
    return os.path.join(os.path.dirname(sys.executable), "gab")