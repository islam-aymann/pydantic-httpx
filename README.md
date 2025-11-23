# pydantic-httpx

[![CI](https://github.com/islam-aymann/pydantic-httpx/workflows/CI/badge.svg)](https://github.com/islam-aymann/pydantic-httpx/actions)
[![codecov](https://codecov.io/gh/islam-aymann/pydantic-httpx/branch/main/graph/badge.svg)](https://codecov.io/gh/islam-aymann/pydantic-httpx)
[![Python Versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://github.com/islam-aymann/pydantic-httpx)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A type-safe HTTP client library that combines the power of HTTPX with Pydantic validation. Build declarative API clients with automatic response validation, full IDE support, and clean Python syntax inspired by FastAPI.

**Status**: 🚧 Alpha (v0.3.0) - Not yet published to PyPI. Use via GitHub installation.

**Recent Updates** (v0.3.0):
- ✅ Simplified unified API - all endpoints return `DataResponse[T]`
- ✅ Full type safety with `Annotated` syntax (zero type checker errors)
- ✅ Consistent response handling across all endpoints
- ✅ Professional code quality with 96% test coverage
- ✅ Automatic request validation from type hints

## What It Does

`pydantic-httpx` lets you define HTTP API clients using Pydantic models and type hints, inspired by FastAPI's approach. Instead of manually constructing requests and parsing responses, you declare your API structure once and get:

- **Unified API**: All endpoints return `DataResponse[T]` wrapper with validated data and HTTP metadata
- Automatic validation of requests and responses with Pydantic
- Full type safety and IDE autocomplete with `Annotated` syntax
- Clean, declarative API definitions
- All HTTPX features (auth, cookies, timeouts, etc.)
- Both sync and async support with the same resource definitions

## Features

- ✅ **Unified API**: All endpoints return `DataResponse[T]` with validated data and HTTP metadata
- ✅ **Type-Safe**: Full type hints with `Annotated` syntax for zero type checker errors
- ✅ **Pydantic Integration**: Automatic request/response validation using Pydantic models
- ✅ **Flexible Organization**: Define endpoints directly on clients or group them in resources
- ✅ **Config-Driven**: Familiar `client_config` and `resource_config` (like Pydantic's `model_config`)
- ✅ **Rich Error Handling**: Detailed exceptions with response context
- ✅ **Full HTTPX Integration**: Query params, headers, cookies, auth, timeouts, redirects
- ✅ **URL Encoding**: Automatic encoding of special characters in path parameters
- ✅ **Sync & Async**: Full support for both sync and async HTTP clients

## Quick Example

### Basic Endpoint Definition

```python
from typing import Annotated
from pydantic import BaseModel
from pydantic_httpx import Client, ClientConfig, Endpoint, GET

# Define your model
class User(BaseModel):
    id: int
    name: str
    email: str

# Define your client with Annotated syntax
class APIClient(Client):
    # Constructor syntax provides full IDE autocomplete
    client_config = ClientConfig(
        base_url="https://api.example.com",
        timeout=30.0,
    )

    # Endpoint[T] returns DataResponse[T]
    get_user: Annotated[Endpoint[User], GET("/users/{id}")]

# Use it - returns DataResponse[User]!
client = APIClient()
response = client.get_user(id=1)  # Type: DataResponse[User]
print(response.status_code)  # 200
print(response.data.name)  # Access validated data
print(response.headers)  # Access response headers
```

### Resource-Based Organization

```python
from pydantic_httpx import BaseResource, ResourceConfig, POST

# Group related endpoints in a resource
class UserResource(BaseResource):
    resource_config = ResourceConfig(prefix="/users")

    get: Annotated[Endpoint[User], GET("/{id}")]
    list_all: Annotated[Endpoint[list[User]], GET("")]
    create: Annotated[Endpoint[User], POST("")]

# Define your client with resources
class APIClient(Client):
    client_config = ClientConfig(base_url="https://api.example.com")

    users: UserResource

# Use it - all endpoints return DataResponse[T]!
client = APIClient()
user_response = client.users.get(id=1)
print(user_response.data.name)  # Access data via .data property

users_response = client.users.list_all()
print(len(users_response.data))  # List of users

new_user_response = client.users.create(json={"name": "John", "email": "john@example.com"})
print(new_user_response.status_code)  # 201
```

### Automatic Request Validation

Add a Pydantic model as the second type parameter for automatic request body validation:

```python
from pydantic import BaseModel

class CreateUserRequest(BaseModel):
    name: str
    email: str

class UserResource(BaseResource):
    resource_config = ResourceConfig(prefix="/users")

    # Second type parameter enables automatic request validation
    create: Annotated[Endpoint[User, CreateUserRequest], POST("")]

# Use it - request body is automatically validated!
client = APIClient()
response = client.users.create(json={"name": "John", "email": "john@example.com"})  # ✅ Valid
print(response.data.name)  # "John"
# client.users.create(json={"name": "John"})  # ❌ Raises ValidationError (missing email)
```

**Key points:**
- First type parameter: Response type (what the endpoint returns)
- Second type parameter (optional): Request model for automatic validation
- Omit second parameter for GET/DELETE endpoints (no request body)
- Request validation happens automatically before sending the request

### Configuration Flexibility

All examples in this documentation use the **constructor syntax** (recommended):

```python
from pydantic_httpx import ClientConfig, ResourceConfig

# Constructor syntax - full IDE autocomplete and type checking!
class APIClient(Client):
    client_config = ClientConfig(
        base_url="https://api.example.com",
        timeout=30.0,
        headers={"User-Agent": "my-app/1.0"},
    )

class UserResource(BaseResource):
    resource_config = ResourceConfig(
        prefix="/users",
        timeout=60.0,
    )
```

Alternative styles are also supported (for compatibility):

```python
# Dict literal with type hint (partial autocomplete)
class APIClient(Client):
    client_config: ClientConfig = {
        "base_url": "https://api.example.com",
        "timeout": 30.0,
    }

# Plain dict (no autocomplete)
class APIClient(Client):
    client_config = {"base_url": "https://api.example.com"}
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
        response = await client.users.get(id=1)  # Returns DataResponse[User]
        print(response.data.name)  # Access validated data
        print(response.status_code)  # Access metadata
```

Or with direct endpoints:

```python
class AsyncAPIClient(AsyncClient):
    client_config = ClientConfig(base_url="https://api.example.com")

    get_user: Annotated[Endpoint[User], GET("/users/{id}")]

async def main():
    async with AsyncAPIClient() as client:
        response = await client.get_user(id=1)  # Returns DataResponse[User]
        print(response.data.name)
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
    search: Annotated[Endpoint[list[User]], GET("/search", query_model=SearchParams)]

# Usage - automatic validation
client = APIClient()
response = client.users.search(status="active", limit=5)
print(len(response.data))  # List of users
```

### Authentication, Headers, and Timeouts

```python
from httpx import BasicAuth

class UserResource(BaseResource):
    resource_config = ResourceConfig(prefix="/users")

    # Custom headers and auth
    protected: Annotated[
        Endpoint[User],
        GET("/{id}", headers={"X-API-Version": "v1"}, auth=BasicAuth("user", "pass"))
    ]

    # Custom timeout and cookies
    slow_endpoint: Annotated[
        Endpoint[dict],
        GET("/data", timeout=30.0, cookies={"session": "abc123"})
    ]
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
- typing-extensions >= 4.4.0 (for optional type parameters)

## API Design

### Unified Endpoint API

All endpoints use `Endpoint[T, TRequest]` with `Annotated` syntax for full type safety:

- **Type-safe declarations**: `Annotated[Endpoint[User], GET("/users/{id}")]`
- **Returns DataResponse[T]**: Access both validated data and HTTP metadata
- **Optional request validation**: Add second type parameter for automatic validation
- **Zero type checker errors**: Full IDE support with Annotated syntax

**Type Parameters**:
1. **T** (required): Response type - what the endpoint returns (e.g., `User`, `list[User]`, `dict`)
2. **TRequest** (optional): Request model for automatic request body validation

**Examples**:
```python
# Simple endpoint - response only
get_user: Annotated[Endpoint[User], GET("/users/{id}")]

# With request validation
create_user: Annotated[Endpoint[User, CreateUserRequest], POST("/users")]

# List response
list_users: Annotated[Endpoint[list[User]], GET("/users")]
```

### Flexible Organization

Define endpoints in two ways:

1. **Direct on Client** - For simple APIs
   ```python
   class APIClient(Client):
       get_user: Annotated[Endpoint[User], GET("/users/{id}")]
   ```

2. **Grouped in Resources** - For larger APIs
   ```python
   class UserResource(BaseResource):
       resource_config = ResourceConfig(prefix="/users")
       get: Annotated[Endpoint[User], GET("/{id}")]
       list_all: Annotated[Endpoint[list[User]], GET("")]
   ```

## Validators

Add custom validation, transformation, or control logic to endpoints using the `@endpoint_validator` decorator (Pydantic-style):

### Before Validators

Transform or validate parameters before the request:

```python
from pydantic_httpx import Client, GET, Endpoint, endpoint_validator

class APIClient(Client):
    client_config = ClientConfig(base_url="https://api.example.com")

    get_user: Annotated[Endpoint[User], GET("/users/{id}")]

    @endpoint_validator("get_user", mode="before")
    def validate_id(cls, params: dict) -> dict:
        """Validate ID before making request."""
        if params.get("id", 0) <= 0:
            raise ValueError("User ID must be positive")
        return params

client = APIClient()
response = client.get_user(id=1)  # ✅ Valid
# client.get_user(id=0)  # ❌ Raises ValueError
```

### After Validators

Transform the response after the request:

```python
class APIClient(Client):
    client_config = ClientConfig(base_url="https://api.example.com")

    get_user: Annotated[Endpoint[User], GET("/users/{id}")]

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

    get_user: Annotated[Endpoint[User], GET("/users/{id}")]

    _cache: dict[int, DataResponse[User]] = {}

    @endpoint_validator("get_user", mode="wrap")
    def cache_user(cls, handler, params: dict) -> DataResponse[User]:
        """Cache user responses."""
        user_id = params["id"]

        # Check cache
        if user_id in cls._cache:
            return cls._cache[user_id]

        # Call the actual request
        response = handler(params)
        cls._cache[user_id] = response
        return response

client = APIClient()
response1 = client.get_user(id=1)  # Hits API
response2 = client.get_user(id=1)  # Returns cached
```

### Resource Validators

Validators can also be defined on resource classes:

```python
class UserResource(BaseResource):
    resource_config = ResourceConfig(prefix="/users")

    get: Annotated[Endpoint[User], GET("/{id}")]

    @endpoint_validator("get", mode="before")
    def validate_get_id(cls, params: dict) -> dict:
        if params.get("id", 0) < 1:
            raise ValueError("ID must be at least 1")
        return params

class APIClient(Client):
    client_config = ClientConfig(base_url="https://api.example.com")
    users: UserResource

client = APIClient()
response = client.users.get(id=5)  # ✅ Valid
# client.users.get(id=0)  # ❌ Raises ValueError
```

## Current Features

### ✅ Complete
- **Unified API**: All endpoints return `DataResponse[T]` wrapper
- **Type-safe**: Full IDE autocomplete and mypy validation with `Annotated` syntax
- **Sync & Async**: `Client` and `AsyncClient` with same resource definitions
- **Pydantic validation**: Request/response models with automatic validation
- **Endpoint validators**: Three modes (before/after/wrap) for custom logic
- **Flexible organization**: Direct endpoints or resource-based grouping
- **HTTPX integration**: Query params, headers, auth, cookies, timeouts, redirects
- **URL encoding**: Automatic encoding of path parameters
- **Error handling**: Rich exceptions with response context

### 📋 Roadmap

**High Priority Features:**
- 🔄 Retry logic with exponential backoff
- 🎣 Global hooks/middleware system
- 📡 Streaming support (SSE, file uploads/downloads)

**Medium Priority:**
- 🔐 Advanced OAuth2 flows with token refresh
- 🔀 Union response types (different models per status code)
- 📄 Pagination support (offset, cursor, page-based)
- ⏱️ Rate limiting with automatic backoff
- 📁 File uploads with multipart forms

**Developer Experience:**
- 📚 Documentation site (MkDocs/Sphinx)
- 🎯 Example integrations (GitHub, Stripe, OpenAI APIs)
- 🧪 Enhanced testing utilities

**Long-term:**
- GraphQL support
- WebSocket endpoints
- Plugin system

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

# (Optional) Install pre-commit hooks for automatic checks
make pre-commit-install

# Run all checks (lint, format, type-check, test)
make check
```

### Available Commands

```bash
make help                 # Show all available commands
make install              # Install package
make install-dev          # Install with dev dependencies
make test                 # Run tests
make test-cov             # Run tests with coverage
make lint                 # Check code with ruff
make lint-fix             # Auto-fix linting issues
make format               # Format code with ruff
make format-check         # Check formatting without changes
make type-check           # Run mypy type checker
make check                # Run all checks
make clean                # Remove build artifacts
make build                # Build distribution packages
make pre-commit-install   # Install pre-commit hooks
make pre-commit-run       # Run pre-commit on all files
```

## License

MIT
