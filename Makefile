.PHONY: install test lint format

install:
    uv sync --extra dev

test:
    uv run pytest

lint:
    uv run ruff check .

format:
    uv run ruff format .
