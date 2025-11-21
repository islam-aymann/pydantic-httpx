"""Type definitions and protocols for pydantic-httpx."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from pydantic_httpx.response import DataResponse

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


class CallableEndpoint(Protocol[T]):
    """
    Protocol for callable endpoints with proper typing.

    This protocol enables IDEs to understand that endpoint descriptors
    are callable and return DataResponse[T].

    Example:
        >>> class UserResource(BaseResource):
        >>>     get: EndpointMethod[User] = GET("/{id}")
        >>>
        >>> # IDE understands that client.users.get(id=1) returns DataResponse[User]
        >>> response = client.users.get(id=1)
    """

    def __call__(self, **kwargs: Any) -> DataResponse[T]:
        """
        Execute the endpoint with the provided parameters.

        Args:
            **kwargs: Path parameters, query parameters, or request body data.

        Returns:
            DataResponse[T]: Response wrapper containing validated data.
        """
        ...


# Type alias for endpoint definitions in resources
# Usage: endpoint: EndpointMethod[User] = GET("/{id}")
# At runtime: client.users.endpoint(id=1) returns DataResponse[User]
EndpointMethod: TypeAlias = CallableEndpoint[T]
