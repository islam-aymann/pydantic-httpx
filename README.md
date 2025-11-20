# pydantic-httpx

Integration library for HTTPX with Pydantic models for type-safe HTTP client requests and responses.

## Installation

```bash
pip install pydantic-httpx
```

## Development

This project uses `uv` for dependency management and includes a Makefile for common tasks.

### Quick Start

```bash
# Create virtual environment
make venv
source .venv/Scripts/activate  # On Windows Git Bash
# or
source .venv/bin/activate      # On Unix/macOS

# Install with development dependencies
make install-dev

# Run all checks (lint, format, type-check, test)
make check
```

### Available Commands

```bash
make help          # Show all available commands
make install       # Install package
make install-dev   # Install with dev dependencies
make test          # Run tests
make test-cov      # Run tests with coverage
make lint          # Check code with ruff
make lint-fix      # Auto-fix linting issues
make format        # Format code with ruff
make format-check  # Check formatting without changes
make type-check    # Run mypy type checker
make check         # Run all checks
make clean         # Remove build artifacts
make build         # Build distribution packages
```

## License

MIT
