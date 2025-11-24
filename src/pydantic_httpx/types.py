"""Type definitions and protocols for pydantic-httpx."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias, overload

from pydantic import BaseModel
from typing_extensions import TypeVar

if TYPE_CHECKING:
    from pydantic_httpx.response import DataResponse

T = TypeVar("T")
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


VALID_HTTP_METHODS: set[str] = {method.value for method in HTTPMethod}
RequestModel: TypeAlias = type[BaseModel] | None
ResponseModel: TypeAlias = (
    type[BaseModel] | type[list[BaseModel]] | type[dict[str, Any]] | type[None]
)

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
        >>> response = client.users.get(path={"id": 1})  # Type: DataResponse[User]
        >>> print(f"Status: {response.status_code}")
        >>> print(f"User: {response.data.name}")
    """

    @overload
    def __call__(
        self,
        *,
        path: dict[str, Any] | None = None,
        params: BaseModel | dict[str, Any] | None = None,
        json: dict[str, Any],
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> DataResponse[T]: ...

    @overload
    def __call__(
        self,
        *,
        path: dict[str, Any] | None = None,
        params: BaseModel | dict[str, Any] | None = None,
        data: BaseModel | dict[str, Any],
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> DataResponse[T]: ...

    @overload
    def __call__(
        self,
        *,
        path: dict[str, Any] | None = None,
        params: BaseModel | dict[str, Any] | None = None,
        content: bytes,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> DataResponse[T]: ...

    @overload
    def __call__(
        self,
        *,
        path: dict[str, Any] | None = None,
        params: BaseModel | dict[str, Any] | None = None,
        files: dict[str, Any],
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> DataResponse[T]: ...

    @overload
    def __call__(
        self,
        *,
        path: dict[str, Any] | None = None,
        params: BaseModel | dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> DataResponse[T]: ...

    def __call__(
        self,
        *,
        path: dict[str, Any] | None = None,
        params: BaseModel | dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: BaseModel | dict[str, Any] | None = None,
        content: bytes | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> DataResponse[T]:
        """
        Execute the endpoint and return full response wrapper.

        Args:
            path: Path parameters as dict (e.g., {"id": 1} for /{id}).
            params: Query parameters - accepts Pydantic BaseModel or dict.
                    If endpoint has query_model, validates dict against it.
            json: JSON request body as dict (will be serialized to JSON).
            data: Request body data - accepts Pydantic BaseModel or dict.
                  If endpoint has request_model, validates dict against it.
            content: Raw bytes content for request body.
            files: Files to upload as multipart/form-data.
            headers: Custom HTTP headers.
            cookies: Custom cookies.
            timeout: Request timeout in seconds (overrides client/endpoint timeout).

        Returns:
            DataResponse[T]: Response wrapper with validated data and metadata.

        Note:
            - Body parameters (json, data, content, files) are mutually exclusive
            - Path parameters: Passed as path dict (e.g., path={"id": 1})
            - Query parameters: Passed as params dict/model
            - Request body: Use json, data, content, or files (only one)
        """
        ...
