# List available commands
list:
    @just --list

# Run typecheck
typecheck:
    uv run mypy . --implicit-optional

# Run formatter
format:
    uv run ruff check --select I --fix
    uv run ruff check . --fix

# Run formatter - no fix
format-check:
    uv run ruff check --select I 
    uv run ruff check .

# Run unit and CLI tests, fail on first test failure
# REVIEW: We should refactor the tests so we can use -nauto here
test:
    uv run pytest  -x --ignore=tests/integration/ --ignore=tests/zksync/

# Run the last failed test
test-lf:
    uv run pytest --lf --ignore=tests/integration/ --ignore=tests/zksync/

# Run integration tests, read the README.md in the tests/integration directory for more information
test-i:
    uv run pytest tests/integration -x --ignore=tests/zksync/  

# Run zksync tests
test-z:
    uv run pytest tests/zksync -nauto --ignore=tests/integration/

# Run both unit and integration tests
test-all:
    @just test
    @just test-i
    @just test-z

# Run tests, fail on first test failure, enter debugger on failure
test-pdb:
    uv run pytest -x -s --ignore=tests/integration/ --ignore=tests/zksync/ --pdb

# For when you want to run the same anvil chain as what's used in the tests
anvil:
    anvil --load-state tests/data/anvil_data/state.json


# Build documentation
docs:
    rm -rf built_docs
    uv sync --extra docs
    uv run python docs/source/_generate_vars.py
    uv run sphinx-build -M html docs/source built_docs -v
    @echo "\nDocumentation link:"
    @echo "http://127.0.0.1:5500/built_docs/html/index.html"

docs-watch:
    watchmedo shell-command --patterns="*.rst" --recursive --command='uv run sphinx-build -M html docs/source built_docs' docs/source

build-requirements:
    uv pip compile pyproject.toml -o requirements.txt