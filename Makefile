.PHONY: test test-security lint all clean

test:
	pytest

test-security:
	bandit -r forenchain/ -c pyproject.toml
	pip-audit

lint:
	ruff check forenchain/ tests/
	mypy forenchain/

all: lint test-security test

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage
