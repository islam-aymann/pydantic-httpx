"""Type definitions and protocols for pydantic-httpx."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias

from pydantic import BaseModel
from typing_extensions import TypeVar

if TYPE_CHECKING:
    from pydantic_httpx.response import DataResponse

# TypeVars for Endpoint type parameters
T_co = TypeVar("T_co", covariant=True)  # Response type (covariant for Endpoint)
T = TypeVar("T")  # Response type (invariant for ResponseEndpoint)
# Request type with default=None (makes second parameter optional)
T_Request = TypeVar("T_Request", covariant=True, default=None)


class HTTPMethod(str, Enum):
    """HTTP method enumeration."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


# Valid HTTP methods as a set (for validation)
VALID_HTTP_METHODS: set[str] = {method.value for method in HTTPMethod}

# Request/Response Models
RequestModel: TypeAlias = type[BaseModel] | None
ResponseModel: TypeAlias = (
    type[BaseModel] | type[list[BaseModel]] | type[dict[str, Any]] | type[None]
)

# Common type aliases
Headers: TypeAlias = dict[str, str]
QueryParams: TypeAlias = dict[str, Any]
PathParams: TypeAlias = dict[str, Any]


class Endpoint(Protocol[T_co, T_Request]):
    """
    Protocol for endpoints that return data directly (auto-extracts response.data).

    This is the default endpoint type for simple cases where you only need
    the validated data, not the full HTTP response metadata.

    Type Parameters:
        T_co: Response type (covariant) - what the endpoint returns
        T_Request: Optional request model type for automatic validation (default: None)
            - Omit for endpoints without request validation (GET, DELETE, etc.)
            - Specify Pydantic model for automatic request body validation

    Example:
        >>> # GET endpoint - no request body (second param optional)
        >>> get: Endpoint[User] = GET("/{id}")
        >>>
        >>> # POST endpoint with automatic request validation
        >>> create: Endpoint[User, CreateUserRequest] = POST("")
        >>>
        >>> # Returns User directly (not DataResponse[User])
        >>> user = client.users.get(id=1)  # Type: User
        >>> new_user = client.users.create(
        >>>     json={"name": "John", "email": "john@example.com"}
        >>> )
    """

    def __call__(self, **kwargs: Any) -> T_co:
        """
        Execute the endpoint and return validated data directly.

        Args:
            **kwargs: Path parameters, query parameters, or request body data.

        Returns:
            T_co: The validated data (response.data is auto-extracted).
        """
        ...


class ResponseEndpoint(Protocol[T, T_Request]):
    """
    Protocol for endpoints that return full DataResponse[T] wrapper.

    Use this when you need access to HTTP metadata like status codes,
    headers, cookies, or response timing information.

    Type Parameters:
        T: Response type - what the endpoint returns
        T_Request: Optional request model type for automatic validation (default: None)
            - Omit for endpoints without request validation (GET, DELETE, etc.)
            - Specify Pydantic model for automatic request body validation

    Example:
        >>> # GET endpoint - no request body (second param optional)
        >>> get: ResponseEndpoint[User] = GET("/{id}")
        >>>
        >>> # POST endpoint with automatic request validation
        >>> create: ResponseEndpoint[User, CreateUserRequest] = POST("")
        >>>
        >>> # Returns DataResponse[User] with full metadata
        >>> response = client.users.get(id=1)  # Type: DataResponse[User]
        >>> print(f"Status: {response.status_code}")
        >>> print(f"User: {response.data.name}")
    """

    def __call__(self, **kwargs: Any) -> DataResponse[T]:
        """
        Execute the endpoint and return full response wrapper.

        Args:
            **kwargs: Path parameters, query parameters, or request body data.

        Returns:
            DataResponse[T]: Response wrapper with validated data and metadata.
        """
        ...
