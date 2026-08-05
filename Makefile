.PHONY: test lint lean check smoke
test:
	uv run pytest
lint:
	uv run ruff check .
lean:
	lake build
smoke:
	uv run python scripts/check.py
check: lint test lean
