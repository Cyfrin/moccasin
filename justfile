# List available commands
list:
    @just --list

# Run typecheck
typecheck:
    uv run mypy . --implicit-optional

# Run formatter
format:
    uv run ruff check . --fix

# Run tests, fail on first test failure
test:
    uv run pytest -x -s --ignore=tests/data/

# Build documentation
docs:
    uv run sphinx-build -M html docs/source built_docs

build-requirements:
    uv pip compile pyproject.toml -o requirements.txt