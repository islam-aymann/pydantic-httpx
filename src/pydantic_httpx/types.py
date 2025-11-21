"""Type definitions and protocols for pydantic-httpx."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from pydantic_httpx.response import DataResponse

T_co = TypeVar("T_co", covariant=True)
T = TypeVar("T")


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


class Endpoint(Protocol[T_co]):
    """
    Protocol for endpoints that return data directly (auto-extracts response.data).

    This is the default endpoint type for simple cases where you only need
    the validated data, not the full HTTP response metadata.

    Example:
        >>> class UserResource(BaseResource):
        >>>     get: Endpoint[User] = GET("/{id}")
        >>>
        >>> # Returns User directly (not DataResponse[User])
        >>> user = client.users.get(id=1)  # Type: User
        >>> print(user.name)  # Direct access to data
    """

    def __call__(self, **kwargs: Any) -> T_co:
        """
        Execute the endpoint and return validated data directly.

        Args:
            **kwargs: Path parameters, query parameters, or request body data.

        Returns:
            T: The validated data (response.data is auto-extracted).
        """
        ...


class ResponseEndpoint(Protocol[T]):
    """
    Protocol for endpoints that return full DataResponse[T] wrapper.

    Use this when you need access to HTTP metadata like status codes,
    headers, cookies, or response timing information.

    Example:
        >>> class UserResource(BaseResource):
        >>>     get: ResponseEndpoint[User] = GET("/{id}")
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
