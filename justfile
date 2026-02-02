default: lint format check test

# Install dependencies
install:
    uv sync

# Run linting checks
lint:
    uv run ruff check src --exclude '**/data.py'

# Format code
format:
    uv run ruff check --select I --fix src data_gen --exclude '**/data.py'
    uv run ruff format src --exclude '**/data.py'

# Run type checking
check:
    uv run ty check src --exclude '**/data.py'

# Run tests
test:
    uv run pytest tests

# Run tests with coverage
test-cov:
    uv run pytest tests --cov=src/tacular --cov-branch --cov-report=term-missing --cov-report=html --cov-report=xml

codecov-tests:
    uv run pytest tests --cov --junitxml=junit.xml -o junit_family=legacy

test-docs:
    uv run pytest --doctest-modules src

# Generate Data Files
gen:
    just --justfile data_gen/justfile gen

update:
    just --justfile data_gen/justfile update

gen-jsons:
    uv run create_output_jsons.py

# Build documentation
docs:
    cd docs && uv run sphinx-build -b html . _build/html

# Run documentation tests
docs-test:
    cd docs && uv run sphinx-build -b doctest . _build/doctest

# Clean documentation build
docs-clean:
    rm -rf docs/_build

# Build and open documentation
docs-open:
    just docs
    python -c "import webbrowser; webbrowser.open('file://{{justfile_directory()}}/docs/_build/html/index.html')"


pre-release: format lint check test gen-jsons docs-test