default: lint format check test

# Install dependencies
install:
    uv sync

# Run linting checks
lint:
    uv run ruff check src

# Format code
format:
	uv run ruff check --select I --fix src data_gen
	uv run ruff format src

# Run type checking
check:
    uv run ty check src

# Run tests
test:
    uv run pytest tests

test-docs:
    uv run pytest --doctest-modules src

# Generate Data Files
gen:
    just --justfile data_gen/justfile gen

update:
    just --justfile data_gen/justfile update

gen-jsons:
    uv run create_output_jsons.py
