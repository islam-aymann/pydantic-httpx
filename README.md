# pydantic-httpx

A type-safe HTTP client library that combines the power of HTTPX with Pydantic validation. Build declarative, resource-based API clients with automatic request/response validation, full IDE support, and clean Python syntax.

**Status**: 🚧 Under active development - Phase 2 (Core Logic) complete

## What It Does

`pydantic-httpx` lets you define HTTP API clients using Pydantic models and type hints. Instead of manually constructing requests and parsing responses, you declare your API structure once and get:

- Automatic validation of requests and responses
- Full type safety and IDE autocomplete
- Clean, declarative API definitions
- All HTTPX features (auth, cookies, timeouts, etc.)

**Status**: Production-ready for both synchronous and asynchronous HTTP clients.

## Features

- ✅ **Type-Safe**: Full type hints with assignment syntax for IDE autocomplete and mypy validation
- ✅ **Pydantic Integration**: Automatic request/response validation using Pydantic models
- ✅ **Explicit API**: Resource-based organization with clear endpoint definitions
- ✅ **Config-Driven**: Familiar `client_config` and `resource_config` (like Pydantic's `model_config`)
- ✅ **Rich Error Handling**: Detailed exceptions with response context
- ✅ **Full HTTPX Integration**: Query params, headers, cookies, auth, timeouts, redirects
- ✅ **URL Encoding**: Automatic encoding of special characters in path parameters
- ✅ **Sync & Async**: Full support for both sync and async HTTP clients with the same resource definitions

## Quick Example

```python
from pydantic import BaseModel
from pydantic_httpx import (
    BaseClient, BaseResource, GET, POST, DataResponse,
    ClientConfig, ResourceConfig
)

# Define your models
class User(BaseModel):
    id: int
    name: str
    email: str

class CreateUserRequest(BaseModel):
    name: str
    email: str

# Define a resource
class UserResource(BaseResource):
    resource_config = ResourceConfig(prefix="/users")

    get: DataResponse[User] = GET("/{id}")
    list_all: DataResponse[list[User]] = GET("")
    create: DataResponse[User] = POST("", request_model=CreateUserRequest)

# Define your client
class APIClient(BaseClient):
    client_config = ClientConfig(base_url="https://api.example.com")

    users: UserResource

# Use it!
client = APIClient()
user = client.users.get(id=1)
print(user.data.name)  # Type-safe access!
```

### Async Support

The same resource definitions work with async clients:

```python
from pydantic_httpx import AsyncBaseClient

# Define your async client (same resource definitions!)
class AsyncAPIClient(AsyncBaseClient):
    client_config = ClientConfig(base_url="https://api.example.com")

    users: UserResource  # Same resource as sync!

# Use it with async/await!
async def main():
    async with AsyncAPIClient() as client:
        user = await client.users.get(id=1)
        print(user.data.name)  # Type-safe async access!
```

### Advanced Features

```python
from httpx import BasicAuth

# Query parameters with validation
class SearchParams(BaseModel):
    status: str
    limit: int = 10

class UserResource(BaseResource):
    resource_config = ResourceConfig(prefix="/users")

    # Query parameters
    search: DataResponse[list[User]] = GET("/search", query_model=SearchParams)

    # Custom headers and auth
    protected: DataResponse[User] = GET(
        "/{id}",
        headers={"X-API-Version": "v1"},
        auth=BasicAuth("user", "pass")
    )

    # Custom timeout and cookies
    slow_endpoint: DataResponse[dict] = GET(
        "/data",
        timeout=30.0,
        cookies={"session": "abc123"}
    )

# Usage
client = APIClient()
results = client.users.search(status="active", limit=5)
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

### ✅ Phase 2: Core Logic (Complete)
- [x] Endpoint metadata classes (`BaseEndpoint`, `Endpoint`, `GET`, `POST`, etc.)
- [x] BaseResource implementation with descriptor protocol
- [x] BaseClient implementation with HTTPX integration
- [x] Request/response serialization with Pydantic validation
- [x] Path parameter interpolation with URL encoding
- [x] Query parameters (with/without Pydantic validation)
- [x] Custom headers per endpoint
- [x] Custom timeout per endpoint
- [x] Authentication support (Basic, Bearer, custom `httpx.Auth`)
- [x] Cookies support
- [x] Redirect control (`follow_redirects`)
- [x] URL encoding for special characters in path params
- [x] HTTPMethod as str, Enum for better type safety
- [x] Assignment-based API (following modern Python conventions)
- [x] Comprehensive test suite (99 tests, 96% coverage)

### ✅ Phase 3: Async Support (Complete)
- [x] `AsyncBaseClient` wrapping `httpx.AsyncClient`
- [x] Runtime detection in descriptor to return sync or async methods
- [x] Single resource definition works with both sync and async clients
- [x] Async context manager support (`async with`)
- [x] Comprehensive async test suite (8 async tests)
- [x] Full test coverage (107 tests, 93% coverage)

### 📋 Phase 4: Advanced Features (Planned)
- [ ] File uploads and multipart forms
- [ ] Union response types for status codes
- [ ] Middleware/hooks system
- [ ] Retry logic with exponential backoff
- [ ] Request/response logging and debugging

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
