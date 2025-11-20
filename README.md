# pydantic-httpx

Integration library for HTTPX with Pydantic models for type-safe HTTP client requests and responses.

**Status**: 🚧 Under active development - Phase 1 (Foundation) complete

## Features

- ✅ **Type-Safe**: Full type hints with `Annotated` for IDE autocomplete and mypy validation
- ✅ **Pydantic Integration**: Automatic request/response validation using Pydantic models
- ✅ **Explicit API**: Resource-based organization with clear endpoint definitions
- ✅ **Config-Driven**: Familiar `client_config` and `resource_config` (like Pydantic's `model_config`)
- 🚧 **Sync & Async**: Support for both sync and async operations (async coming soon)
- 🚧 **Rich Error Handling**: Detailed exceptions with response context (foundation complete)

## Quick Example (Preview)

```python
from typing import Annotated
from pydantic import BaseModel
from pydantic_httpx import BaseClient, BaseResource, Endpoint, DataResponse, ClientConfig, ResourceConfig

# Define your models
class User(BaseModel):
    id: int
    name: str
    email: str

# Define a resource
class UserResource(BaseResource):
    resource_config = ResourceConfig(prefix="/users")

    get: Annotated[DataResponse[User], Endpoint("GET", "/{id}")]
    list: Annotated[DataResponse[list[User]], Endpoint("GET", "")]
    create: Annotated[DataResponse[User], Endpoint("POST", "", request=CreateUserRequest)]

# Define your client
class APIClient(BaseClient):
    client_config = ClientConfig(base_url="https://api.example.com")

    users: UserResource

# Use it!
client = APIClient()
user = client.users.get(id=1)
print(user.data.name)  # Type-safe access!
```

## Installation

```bash
pip install pydantic-httpx
```

**Note**: Package not yet published to PyPI. Currently in development.

## Development Progress

### ✅ Phase 1: Foundation (Complete)
- [x] Config classes (`ClientConfig`, `ResourceConfig`)
- [x] Exception hierarchy (`ResponseError`, `HTTPError`, `ValidationError`, etc.)
- [x] Response wrapper (`DataResponse[T]`)
- [x] Type definitions
- [x] Comprehensive test suite (37 tests, 92% coverage)

### 🚧 Phase 2: Core Logic (In Progress)
- [ ] Endpoint metadata class
- [ ] BaseResource implementation
- [ ] BaseClient implementation
- [ ] Request/response serialization
- [ ] Path parameter interpolation

### 📋 Phase 3: Advanced Features (Planned)
- [ ] Async support (`AsyncBaseClient`, `AsyncBaseResource`)
- [ ] File uploads and multipart forms
- [ ] Union response types for status codes
- [ ] Middleware/hooks system

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
