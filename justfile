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

test-cov:
    uv run pytest tests --cov=src/tacular --cov-report=term-missing --cov-report=html --cov-report=xml

test-docs:
    uv run pytest --doctest-modules src

# Generate Data Files
gen:
    just --justfile data_gen/justfile gen

update:
    just --justfile data_gen/justfile update

gen-jsons:
    uv run create_output_jsons.py