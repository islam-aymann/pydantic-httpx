.PHONY: help install install-dev clean test test-cov test-watch lint format type-check check build publish-test publish pre-commit-install pre-commit-run

# Default target
help:
	@echo "Available commands:"
	@echo "  make install              Install package in production mode"
	@echo "  make install-dev          Install package with development dependencies"
	@echo "  make clean                Remove build artifacts and cache files"
	@echo "  make test                 Run tests"
	@echo "  make test-cov             Run tests with coverage report"
	@echo "  make test-watch           Run tests in watch mode"
	@echo "  make lint                 Run linter (ruff)"
	@echo "  make lint-fix             Run linter and auto-fix issues"
	@echo "  make format               Format code with ruff"
	@echo "  make format-check         Check code formatting without changes"
	@echo "  make ruff         		   Format code and fix linting issues with ruff"
	@echo "  make type-check           Run type checker (mypy)"
	@echo "  make check                Run all checks (lint, format-check, type-check, test)"
	@echo "  make build                Build distribution packages"
	@echo "  make publish-test         Publish to TestPyPI"
	@echo "  make publish              Publish to PyPI"
	@echo "  make venv                 Create virtual environment"
	@echo "  make pre-commit-install   Install pre-commit hooks"
	@echo "  make pre-commit-run       Run pre-commit on all files"

# Virtual environment
venv:
	uv venv
	@echo "Virtual environment created. Activate with: source .venv/Scripts/activate"

# Installation
install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Testing
test:
	pytest

test-cov:
	pytest --cov --cov-report=html --cov-report=term

test-watch:
	pytest --watch

# Linting
lint:
	ruff check .

lint-fix:
	ruff check --fix .

# Formatting
format:
	ruff format .

format-check:
	ruff format --check .

ruff: lint-fix format

# Type checking
type-check:
	mypy src/

# Run all checks
check: lint format-check type-check test

# Building
build: clean
	uv build

# Publishing
publish-test: build
	uv publish --publish-url https://test.pypi.org/legacy/

publish: build
	uv publish

# Pre-commit hooks
pre-commit-install:
	uv tool install pre-commit
	uv run pre-commit install
	@echo "Pre-commit hooks installed successfully!"

pre-commit-run:
	uv run pre-commit run --all-files
