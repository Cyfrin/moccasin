# List available commands
list:
    @just --list

# Run typecheck
typecheck:
    uv run mypy . --implicit-optional

# Run formatter
format:
    uv run ruff check . --fix

# Run formatter - no fix
format-check:
    uv run ruff check .

# Run unit and CLI tests, fail on first test failure
test:
    uv run pytest -x -s --ignore=tests/data/ --ignore=tests/integration/

# Run integration tests, read the README.md in the tests/integration directory for more information
test-i:
    uv run pytest tests/integration -x -s --ignore=tests/data/ 

# Run both unit and integration tests
test-all:
    @just test
    @just test-i

# Run tests, fail on first test failure, enter debugger on failure
test-pdb:
    uv run pytest -x -s --ignore=tests/data/ --pdb

# Build documentation
docs:
    uv sync --extra docs
    uv run sphinx-build -M html docs/source built_docs

docs-watch:
    watchmedo shell-command --patterns="*.rst" --recursive --command='uv run sphinx-build -M html docs/source built_docs' docs/source

build-requirements:
    uv pip compile pyproject.toml -o requirements.txt