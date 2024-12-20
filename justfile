@_default:
    just --list

# Build a development environment
devenv:
    uv sync --extra dev --refresh --upgrade

# Run tests and linting
test: devenv
    tox

# Format files
format: devenv
    uv run tox exec -e py39-lint -- ruff format

# Lint files
lint: devenv
    uv run tox -e py39-lint

# Wipe dev environment and build artifacts
clean:
    rm -rf build dist src/kent.egg-info .tox .pytest_cache
    find src/ -name __pycache__ | xargs rm -rf
    find src/ -name '*.pyc' | xargs rm -rf

# Build Docker image and run it
testdocker:
    docker build --no-cache -t kent:latest .
    docker run --init --rm --publish 5000:5000 kent:latest run --host 0.0.0.0 --port 5000

# Build files for relase
build: devenv
    rm -rf build/ dist/
    uv run python -m build
    uv run twine check dist/*
