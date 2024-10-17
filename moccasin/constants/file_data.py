GITATTRIBUTES = """
*.sol linguist-language=Solidity
*.vy linguist-language=Python
"""

GITIGNORE = """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
#   For a library or package, you might want to ignore these files since the code is
#   intended to run in multiple environments; otherwise, check them in:
# .python-version

# pipenv
#   According to pypa/pipenv#598, it is recommended to include Pipfile.lock in version control.
#   However, in case of collaboration, if having platform-specific dependencies or dependencies
#   having no cross-platform support, pipenv may install dependencies that don't work, or not
#   install all needed dependencies.
#Pipfile.lock

# poetry
#   Similar to Pipfile.lock, it is generally recommended to include poetry.lock in version control.
#   This is especially recommended for binary packages to ensure reproducibility, and is more
#   commonly ignored for libraries.
#   https://python-poetry.org/docs/basic-usage/#commit-your-poetrylock-file-to-version-control
#poetry.lock

# pdm
#   Similar to Pipfile.lock, it is generally recommended to include pdm.lock in version control.
#pdm.lock
#   pdm stores project-wide configurations in .pdm.toml, but it is recommended to not include it
#   in version control.
#   https://pdm.fming.dev/latest/usage/project/#working-with-version-control
.pdm.toml
.pdm-python
.pdm-build/

# PEP 582; used by e.g. github.com/David-OConnor/pyflow and github.com/pdm-project/pdm
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# PyCharm
#  JetBrains specific template is maintained in a separate JetBrains.gitignore that can
#  be found at https://github.com/github/gitignore/blob/main/Global/JetBrains.gitignore
#  and can be added to the global gitignore or merged into this file.  For a more nuclear
#  option (not recommended) you can uncomment the following to ignore the entire idea folder.
#.idea/

# Ruff / Rye
.ruff_cache

# Moccasin
.env
.env.unsafe
.env*
out/
build/
lib/
.password.unsafe
.password
.password*
.deployments*
.deployments.db
era_test_node.log
"""

COUNTER_VYPER_CONTRACT_SRC = """# SPDX-License-Identifier: MIT
# pragma version 0.4.0

number: public(uint256)

@external
def set_number(new_number: uint256):
    self.number = new_number

@external
def increment():
    self.number += 1
"""

DEPLOY_SCRIPT_DEFAULT = """from src import Counter
from moccasin.boa_tools import VyperContract
# from boa.contracts.vyper.vyper_contract import VyperContract

def deploy() -> VyperContract:
    counter: VyperContract = Counter.deploy()
    print("Starting count: ", counter.number())
    counter.increment()
    print("Ending count: ", counter.number())
    return counter

def moccasin_main() -> VyperContract:
    return deploy()
"""

CONFTEST_DEFAULT = """import pytest
from script.deploy import deploy

@pytest.fixture
def counter_contract():
    return deploy()"""

COVERAGERC = """
[run]
plugins = boa.coverage
"""

TEST_COUNTER_DEFAULT = """def test_increment(counter_contract):
    counter_contract.increment()
    assert counter_contract.number() == 2"""

README_MD_SRC = """# Moccasin Project

🐍 Welcome to your Moccasin project!

## Quickstart

```bash
mox init
mox run deploy
```

_For documentation, please run `mox --help` or visit [the Moccasin documentation](https://cyfrin.github.io/moccasin)_
"""

MOCCASIN_DEFAULT_CONFIG = """[project]
src = "src"
out = "out"
dot_env = ".env"

[networks.pyevm]
is_zksync = false

[networks.anvil]
url = "http://127.0.0.1:8545"
prompt_live = false
save_to_db = false
chain_id = 31337

[networks.sepolia]
url = "https://ethereum-sepolia-rpc.publicnode.com"
chain_id = 11155111

[networks.zksync-sepolia]
url = "https://sepolia.era.zksync.dev"
chain_id = 300
is_zksync = true
prompt_live = true

# You can view all configuration options at https://cyfrin.github.io/moccasin/all_moccasin_toml_parameters.html
"""

VSCODE_SETTINGS_DEFAULT = """{
    "files.exclude": {
        "**/__pycache__": true
    },
    "files.associations": {
        ".coveragerc": "toml"
    },
    "vyper.command": "vyper -p ./lib/github -p ./lib/pypi"
}
"""

PYPROJECT_TOML_DEFAULT = """[project]
name = "moccasin_project"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.11"
dependencies = []
"""
