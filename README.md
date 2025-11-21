# pydantic-httpx

[![CI](https://github.com/islam-aymann/pydantic-httpx/workflows/CI/badge.svg)](https://github.com/islam-aymann/pydantic-httpx/actions)
[![codecov](https://codecov.io/gh/islam-aymann/pydantic-httpx/branch/main/graph/badge.svg)](https://codecov.io/gh/islam-aymann/pydantic-httpx)
[![Python Versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://github.com/islam-aymann/pydantic-httpx)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A type-safe HTTP client library that combines the power of HTTPX with Pydantic validation. Build declarative API clients with automatic request/response validation, full IDE support, and clean Python syntax inspired by FastAPI.

**Status**: 🚧 Alpha (v0.1.0) - Not yet published to PyPI. Use via GitHub installation.

## What It Does

`pydantic-httpx` lets you define HTTP API clients using Pydantic models and type hints, inspired by FastAPI's approach. Instead of manually constructing requests and parsing responses, you declare your API structure once and get:

- **Two endpoint styles**: Simple `Endpoint[T]` returns data directly, `ResponseEndpoint[T]` provides full response metadata
- Automatic validation of requests and responses with Pydantic
- Full type safety and IDE autocomplete
- Clean, declarative API definitions
- All HTTPX features (auth, cookies, timeouts, etc.)
- Both sync and async support with the same resource definitions

## Features

- ✅ **FastAPI-Style API**: Choose between `Endpoint[T]` (returns data) or `ResponseEndpoint[T]` (returns full response)
- ✅ **Type-Safe**: Full type hints with assignment syntax for IDE autocomplete and mypy validation
- ✅ **Pydantic Integration**: Automatic request/response validation using Pydantic models
- ✅ **Flexible Organization**: Define endpoints directly on clients or group them in resources
- ✅ **Config-Driven**: Familiar `client_config` and `resource_config` (like Pydantic's `model_config`)
- ✅ **Rich Error Handling**: Detailed exceptions with response context
- ✅ **Full HTTPX Integration**: Query params, headers, cookies, auth, timeouts, redirects
- ✅ **URL Encoding**: Automatic encoding of special characters in path parameters
- ✅ **Sync & Async**: Full support for both sync and async HTTP clients

## Quick Example

### Simple Endpoint (Returns Data Directly)

```python
from pydantic import BaseModel
from pydantic_httpx import Client, Endpoint, GET, ClientConfig

# Define your model
class User(BaseModel):
    id: int
    name: str
    email: str

# Define your client
class APIClient(Client):
    client_config = ClientConfig(base_url="https://api.example.com")

    # Endpoint[T] returns data directly (no wrapper)
    get_user: Endpoint[User] = GET("/users/{id}")

# Use it - returns User directly!
client = APIClient()
user = client.get_user(id=1)  # Type: User
print(user.name)  # Direct access to data
```

### Full Response Endpoint (Returns Response + Data)

```python
from pydantic_httpx import ResponseEndpoint

class APIClient(Client):
    client_config = ClientConfig(base_url="https://api.example.com")

    # ResponseEndpoint[T] returns DataResponse[T] with metadata
    get_user: ResponseEndpoint[User] = GET("/users/{id}")

# Use it - returns DataResponse[User]!
client = APIClient()
response = client.get_user(id=1)  # Type: DataResponse[User]
print(response.status_code)  # 200
print(response.data.name)  # Access validated data
print(response.headers)  # Access response headers
```

### Resource-Based Organization

```python
from pydantic_httpx import BaseResource, POST, ResourceConfig

class CreateUserRequest(BaseModel):
    name: str
    email: str

# Group related endpoints in a resource
class UserResource(BaseResource):
    resource_config = ResourceConfig(prefix="/users")

    get: Endpoint[User] = GET("/{id}")
    list_all: Endpoint[list[User]] = GET("")
    create: Endpoint[User] = POST("", request_model=CreateUserRequest)

# Define your client with resources
class APIClient(Client):
    client_config = ClientConfig(base_url="https://api.example.com")

    users: UserResource

# Use it!
client = APIClient()
user = client.users.get(id=1)
users = client.users.list_all()
new_user = client.users.create(json={"name": "John", "email": "john@example.com"})
```

## Async Support

The same resource definitions work with async clients:

```python
from pydantic_httpx import AsyncClient

# Define your async client (same resource definitions!)
class AsyncAPIClient(AsyncClient):
    client_config = ClientConfig(base_url="https://api.example.com")

    users: UserResource  # Same resource as sync!

# Use it with async/await!
async def main():
    async with AsyncAPIClient() as client:
        user = await client.users.get(id=1)  # Returns User directly
        print(user.name)  # Type-safe async access!
```

Or with direct endpoints:

```python
class AsyncAPIClient(AsyncClient):
    client_config = ClientConfig(base_url="https://api.example.com")

    get_user: Endpoint[User] = GET("/users/{id}")

async def main():
    async with AsyncAPIClient() as client:
        user = await client.get_user(id=1)  # Returns User directly
        print(user.name)
```

## When to Use Each Endpoint Type

### Use `Endpoint[T]` when:
- You only need the validated data, not response metadata
- You want simpler, cleaner code with direct data access
- Most common use case for REST APIs

```python
get_user: Endpoint[User] = GET("/users/{id}")
user = client.get_user(id=1)  # Returns User directly
print(user.name)  # Clean and simple
```

### Use `ResponseEndpoint[T]` when:
- You need HTTP metadata (status codes, headers, cookies)
- You want to handle different status codes differently
- You need access to response timing or raw response

```python
get_user: ResponseEndpoint[User] = GET("/users/{id}")
response = client.get_user(id=1)  # Returns DataResponse[User]
if response.status_code == 200:
    print(response.data.name)
    print(f"Took {response.elapsed.total_seconds()}s")
```

## Advanced Features

### Query Parameters with Validation

```python
from pydantic_httpx import BaseResource, ResourceConfig

class SearchParams(BaseModel):
    status: str
    limit: int = 10

class UserResource(BaseResource):
    resource_config = ResourceConfig(prefix="/users")

    # With Pydantic validation
    search: Endpoint[list[User]] = GET("/search", query_model=SearchParams)

# Usage - automatic validation
client = APIClient()
results = client.users.search(status="active", limit=5)  # Returns list[User]
```

### Authentication, Headers, and Timeouts

```python
from httpx import BasicAuth

class UserResource(BaseResource):
    resource_config = ResourceConfig(prefix="/users")

    # Custom headers and auth
    protected: ResponseEndpoint[User] = GET(
        "/{id}",
        headers={"X-API-Version": "v1"},
        auth=BasicAuth("user", "pass")
    )

    # Custom timeout and cookies
    slow_endpoint: Endpoint[dict] = GET(
        "/data",
        timeout=30.0,
        cookies={"session": "abc123"}
    )
```

## Installation

**Note**: This package is not yet published to PyPI. Install directly from GitHub:

### Using pip

```bash
pip install git+https://github.com/islam-aymann/pydantic-httpx.git
```

### Using uv (recommended)

```bash
uv add git+https://github.com/islam-aymann/pydantic-httpx.git
```

### Using Poetry

```bash
poetry add git+https://github.com/islam-aymann/pydantic-httpx.git
```

### In pyproject.toml

```toml
[project]
dependencies = [
    "pydantic-httpx @ git+https://github.com/islam-aymann/pydantic-httpx.git",
]
```

### Requirements

- Python 3.10+
- httpx >= 0.27.0
- pydantic >= 2.0.0

## API Design

### Two Endpoint Types

This library provides two ways to define endpoints, inspired by FastAPI's approach:

1. **`Endpoint[T]`** - Returns data directly (most common)
   - Automatically extracts `response.data`
   - Cleaner code for typical use cases
   - Type hint: `Endpoint[User]` → returns `User`

2. **`ResponseEndpoint[T]`** - Returns full response wrapper
   - Access to HTTP metadata (status, headers, cookies, timing)
   - Type hint: `ResponseEndpoint[User]` → returns `DataResponse[User]`

### Flexible Organization

Define endpoints in two ways:

1. **Direct on Client** - For simple APIs
   ```python
   class APIClient(Client):
       get_user: Endpoint[User] = GET("/users/{id}")
   ```

2. **Grouped in Resources** - For larger APIs
   ```python
   class UserResource(BaseResource):
       resource_config = ResourceConfig(prefix="/users")
       get: Endpoint[User] = GET("/{id}")
       list_all: Endpoint[list[User]] = GET("")
   ```

## Validators

Add custom validation, transformation, or control logic to endpoints using the `@endpoint_validator` decorator (Pydantic-style):

### Before Validators

Transform or validate parameters before the request:

```python
from pydantic_httpx import Client, GET, Endpoint, endpoint_validator

class APIClient(Client):
    client_config = ClientConfig(base_url="https://api.example.com")

    get_user: Endpoint[User] = GET("/users/{id}")

    @endpoint_validator("get_user", mode="before")
    def validate_id(cls, params: dict) -> dict:
        """Validate ID before making request."""
        if params.get("id", 0) <= 0:
            raise ValueError("User ID must be positive")
        return params

client = APIClient()
user = client.get_user(id=1)  # ✅ Valid
# client.get_user(id=0)  # ❌ Raises ValueError
```

### After Validators

Transform the response after the request:

```python
class APIClient(Client):
    client_config = ClientConfig(base_url="https://api.example.com")

    get_user: ResponseEndpoint[User] = GET("/users/{id}")

    @endpoint_validator("get_user", mode="after")
    def handle_404(cls, response: DataResponse[User]) -> DataResponse[User | None]:
        """Return None for 404 responses."""
        if response.status_code == 404:
            return DataResponse(response.response, None)
        return response

client = APIClient()
response = client.get_user(id=999)
if response.data is None:
    print("User not found")
```

### Wrap Validators

Full control over request execution (caching, retry, etc.):

```python
class APIClient(Client):
    client_config = ClientConfig(base_url="https://api.example.com")

    get_user: Endpoint[User] = GET("/users/{id}")

    _cache: dict[int, User] = {}

    @endpoint_validator("get_user", mode="wrap")
    def cache_user(cls, handler, params: dict) -> User:
        """Cache user responses."""
        user_id = params["id"]

        # Check cache
        if user_id in cls._cache:
            return cls._cache[user_id]

        # Call the actual request
        response = handler(params)
        cls._cache[user_id] = response.data
        return response.data

client = APIClient()
user1 = client.get_user(id=1)  # Hits API
user2 = client.get_user(id=1)  # Returns cached
```

### Resource Validators

Validators can also be defined on resource classes:

```python
class UserResource(BaseResource):
    resource_config = ResourceConfig(prefix="/users")

    get: Endpoint[User] = GET("/{id}")

    @endpoint_validator("get", mode="before")
    def validate_get_id(cls, params: dict) -> dict:
        if params.get("id", 0) < 1:
            raise ValueError("ID must be at least 1")
        return params

class APIClient(Client):
    client_config = ClientConfig(base_url="https://api.example.com")
    users: UserResource

client = APIClient()
user = client.users.get(id=5)  # ✅ Valid
# client.users.get(id=0)  # ❌ Raises ValueError
```

## Current Features

### ✅ Complete
- **Two endpoint types**: `Endpoint[T]` and `ResponseEndpoint[T]`
- **Sync & Async**: `Client` and `AsyncClient` with same resource definitions
- **Type-safe**: Full IDE autocomplete and mypy validation
- **Pydantic validation**: Request/response models with automatic validation
- **Endpoint validators**: Three modes (before/after/wrap) for custom logic
- **Flexible organization**: Direct endpoints or resource-based grouping
- **HTTPX integration**: Query params, headers, auth, cookies, timeouts, redirects
- **URL encoding**: Automatic encoding of path parameters
- **Error handling**: Rich exceptions with response context
- **125 tests, 92% coverage**

### 📋 Planned
- File uploads and multipart forms
- Union response types for different status codes
- Retry logic with exponential backoff
- Request/response logging and debugging

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
