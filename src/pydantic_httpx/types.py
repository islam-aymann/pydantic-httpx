"""Type definitions and protocols for pydantic-httpx."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias, overload

from httpx._types import AuthTypes, RequestExtensions, TimeoutTypes
from httpx._types import CookieTypes as HttpxCookieTypes
from httpx._types import HeaderTypes as HttpxHeaderTypes
from httpx._types import QueryParamTypes as HttpxQueryParamTypes
from httpx._types import RequestContent as HttpxRequestContent
from httpx._types import RequestData as HttpxRequestData
from httpx._types import RequestFiles as HttpxRequestFiles
from pydantic import BaseModel
from typing_extensions import TypeVar

if TYPE_CHECKING:
    from pydantic_httpx.response import DataResponse

T = TypeVar("T")
T_Request_co = TypeVar("T_Request_co", covariant=True, default=None)
T_Query_co = TypeVar("T_Query_co", covariant=True, default=None)
T_Path_co = TypeVar("T_Path_co", covariant=True, default=None)
T_Headers_co = TypeVar("T_Headers_co", covariant=True, default=None)
T_Cookies_co = TypeVar("T_Cookies_co", covariant=True, default=None)


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

QueryParamTypes: TypeAlias = BaseModel | HttpxQueryParamTypes
HeaderTypes: TypeAlias = BaseModel | HttpxHeaderTypes
CookieTypes: TypeAlias = BaseModel | HttpxCookieTypes
PathParamTypes: TypeAlias = BaseModel | dict[str, Any]
RequestData: TypeAlias = BaseModel | HttpxRequestData
RequestContent: TypeAlias = HttpxRequestContent
RequestFiles: TypeAlias = HttpxRequestFiles

Headers: TypeAlias = dict[str, str]
QueryParams: TypeAlias = dict[str, Any]
PathParams: TypeAlias = dict[str, Any]


class Endpoint(
    Protocol[T, T_Request_co, T_Query_co, T_Path_co, T_Headers_co, T_Cookies_co]
):
    """
    Protocol for type-safe HTTP endpoints with validation.

    Type Parameters:
        T: Response model type
        T_Request_co: Request body validation model (optional)
        T_Query_co: Query parameters validation model (optional)
        T_Path_co: Path parameters validation model (optional)
        T_Headers_co: Headers validation model (optional)
        T_Cookies_co: Cookies validation model (optional)

    Example:
        >>> get: Annotated[Endpoint[User], GET("/{id}")]
        >>> create: Annotated[Endpoint[User, CreateUserRequest], POST("")]
        >>> search: Annotated[Endpoint[list[User], None, SearchParams], GET("/search")]
    """

    @overload
    def __call__(
        self,
        *,
        path: PathParamTypes | None = None,
        params: QueryParamTypes | None = None,
        json: dict[str, Any],
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        auth: AuthTypes | None = None,
        follow_redirects: bool | None = None,
        timeout: TimeoutTypes | None = None,
        extensions: RequestExtensions | None = None,
    ) -> DataResponse[T]: ...

    @overload
    def __call__(
        self,
        *,
        path: PathParamTypes | None = None,
        params: QueryParamTypes | None = None,
        data: RequestData,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        auth: AuthTypes | None = None,
        follow_redirects: bool | None = None,
        timeout: TimeoutTypes | None = None,
        extensions: RequestExtensions | None = None,
    ) -> DataResponse[T]: ...

    @overload
    def __call__(
        self,
        *,
        path: PathParamTypes | None = None,
        params: QueryParamTypes | None = None,
        content: RequestContent,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        auth: AuthTypes | None = None,
        follow_redirects: bool | None = None,
        timeout: TimeoutTypes | None = None,
        extensions: RequestExtensions | None = None,
    ) -> DataResponse[T]: ...

    @overload
    def __call__(
        self,
        *,
        path: PathParamTypes | None = None,
        params: QueryParamTypes | None = None,
        files: RequestFiles,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        auth: AuthTypes | None = None,
        follow_redirects: bool | None = None,
        timeout: TimeoutTypes | None = None,
        extensions: RequestExtensions | None = None,
    ) -> DataResponse[T]: ...

    @overload
    def __call__(
        self,
        *,
        path: PathParamTypes | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        auth: AuthTypes | None = None,
        follow_redirects: bool | None = None,
        timeout: TimeoutTypes | None = None,
        extensions: RequestExtensions | None = None,
    ) -> DataResponse[T]: ...

    def __call__(
        self,
        *,
        path: PathParamTypes | None = None,
        params: QueryParamTypes | None = None,
        json: Any | None = None,
        data: RequestData | None = None,
        content: RequestContent | None = None,
        files: RequestFiles | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        auth: AuthTypes | None = None,
        follow_redirects: bool | None = None,
        timeout: TimeoutTypes | None = None,
        extensions: RequestExtensions | None = None,
    ) -> DataResponse[T]:
        """Execute endpoint and return validated response."""
        ...
