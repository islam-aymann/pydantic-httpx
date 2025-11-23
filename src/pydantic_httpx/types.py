"""Type definitions and protocols for pydantic-httpx."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias

from pydantic import BaseModel
from typing_extensions import TypeVar

if TYPE_CHECKING:
    from pydantic_httpx.response import DataResponse

# TypeVars for Endpoint type parameters
T = TypeVar("T")  # Response type for Endpoint
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


class Endpoint(Protocol[T, T_Request]):
    """
    Protocol for endpoints that return DataResponse[T] wrapper.

    All endpoints return DataResponse[T] which includes both the validated data
    and HTTP metadata like status codes, headers, cookies, and timing information.

    Type Parameters:
        T: Response type - the data type wrapped in DataResponse[T]
        T_Request: Optional request model type for automatic validation (default: None)
            - Omit for endpoints without request validation (GET, DELETE, etc.)
            - Specify Pydantic model for automatic request body validation

    Example:
        >>> # GET endpoint - no request body (second param optional)
        >>> get: Annotated[Endpoint[User], GET("/{id}")]
        >>>
        >>> # POST endpoint with automatic request validation
        >>> create: Annotated[Endpoint[User, CreateUserRequest], POST("")]
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
