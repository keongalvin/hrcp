set dotenv-load

CHECK := " ✅"
CROSS := " ❌"
WARN := " ⚠️"

# ruff config
RUFF_FORMAT_PATHS := "src scripts tests"

@_:
    just --list --unsorted

alias fmt := format

# === Main ===
# Run formatters
[group('main')]
format:
    @just python-format

# Run linters
[group('qa')]
lint path="":
    just python-lint {{path}}


# Run tests
[group('qa')]
test path="." *args:
    uv run pytest {{ path }} {{ args }}

## === PYTHON LIBRARY DEVELOPMENT ===

# Verify if uv is installed
[group('python-dev')]
check-uv: (check-tool "uv" "https://docs.astral.sh/uv/#installation")


[group('python-dev')]
python-format:
    @uvx ruff check check --exit-zero --no-cache --force-exclude --unsafe-fixes --fix {{RUFF_FORMAT_PATHS}}
    @uvx ruff format {{RUFF_FORMAT_PATHS}}

# Run linters.
[group('python-dev')]
python-lint:
    uvx ruff check
    uvx ruff format
    uvx ty check --python .venv src

# Update dependencies.
[group('python-dev')]
update:
    uv sync --upgrade

# Ensure project virtualenv is up to date.
[group('python-dev')]
install:
    uv sync --all-extras

# Remove temporary files
[group('lifecycle')]
clean:
    rm -rf .venv .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov dist
    find . -type d -name "__pycache__" -exec rm -r {} +


# Recreate project virtualenv from nothing
[group('lifecycle')]
fresh: clean install

# === Utils ===
[private]
check-tool tool install_url:
    @which {{tool}} > /dev/null 2>&1 && echo "{{CHECK}} {{tool}} installed" || echo "{{CROSS}} {{tool}} not found. Install: {{install_url}}"
