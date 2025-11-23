"""Endpoint metadata for HTTP operations."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, overload
from urllib.parse import quote

import httpx
from pydantic import BaseModel

from pydantic_httpx.types import HTTPMethod

if TYPE_CHECKING:
    from pydantic_httpx.response import DataResponse


@dataclass
class BaseEndpoint:
    """
    Base endpoint class without method validation.

    This is the base class for all endpoint types. It provides common
    functionality for path handling and parameter extraction.

    Attributes:
        method: HTTP method enum.
        path: URL path template with optional parameters (e.g., "/{id}").
        query_model: Optional Pydantic model for query parameters.
        timeout: Optional request-specific timeout override.
        headers: Optional request-specific headers.
        cookies: Optional request-specific cookies.
        auth: Optional authentication (Basic, Digest, Bearer, or custom).
        follow_redirects: Optional override for redirect following behavior.
    """

    method: HTTPMethod
    path: str
    query_model: type[BaseModel] | None = None
    timeout: float | None = None
    headers: dict[str, str] = field(default_factory=dict)
    cookies: dict[str, str] | None = None
    auth: httpx.Auth | tuple[str, str] | str | None = None
    follow_redirects: bool | None = None

    def __post_init__(self) -> None:
        """Normalize path after initialization."""
        # Ensure path starts with / (empty path becomes /)
        if not self.path:
            self.path = "/"
        elif not self.path.startswith("/"):
            self.path = f"/{self.path}"

    def get_path_params(self) -> list[str]:
        """
        Extract path parameter names from the path template.

        Returns:
            List of parameter names found in the path (e.g., ["id", "name"]).

        Example:
            >>> endpoint = GET("/users/{id}/posts/{post_id}")
            >>> endpoint.get_path_params()
            ['id', 'post_id']
        """
        # Match {param_name} patterns
        pattern = r"\{([^}]+)\}"
        return re.findall(pattern, self.path)

    def format_path(self, **params: Any) -> str:
        """
        Format the path template with provided parameters.

        Args:
            **params: Path parameters to substitute into the template.

        Returns:
            Formatted path string.

        Raises:
            ValueError: If required path parameters are missing.

        Example:
            >>> endpoint = GET("/users/{id}")
            >>> endpoint.format_path(id=123)
            '/users/123'
        """
        required_params = self.get_path_params()
        missing_params = set(required_params) - set(params.keys())

        if missing_params:
            raise ValueError(f"Missing required path parameters: {missing_params}")

        # Replace {param} with actual values (URL-encoded)
        path = self.path
        for param_name, param_value in params.items():
            # URL-encode the parameter value (safe='' means encode everything)
            encoded_value = quote(str(param_value), safe="")
            path = path.replace(f"{{{param_name}}}", encoded_value)

        return path

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.method=}, {self.path=})"

    if TYPE_CHECKING:

        @overload
        def __get__(self, instance: None, owner: type) -> BaseEndpoint: ...

        @overload
        def __get__(
            self, instance: object, owner: type
        ) -> Callable[..., DataResponse[Any] | Awaitable[DataResponse[Any]]]: ...

        def __get__(
            self, instance: object | None, owner: type
        ) -> (
            BaseEndpoint
            | Callable[..., DataResponse[Any] | Awaitable[DataResponse[Any]]]
        ):
            """
            Descriptor protocol for type checking only.

            At runtime, endpoints are replaced by EndpointDescriptor.
            """
            ...

        def __call__(self, **kwargs: Any) -> DataResponse[Any]:
            """Type hint for IDE support (never called at runtime)."""
            ...


@dataclass
class Endpoint(BaseEndpoint):
    """
    Generic endpoint with method validation.

    Use this when you need to specify the HTTP method dynamically.
    For static methods, prefer using GET, POST, DELETE, etc. directly.

    Example:
        >>> from pydantic_httpx import Endpoint, HTTPMethod
        >>> endpoint = Endpoint(HTTPMethod.GET, "/{id}")
        >>> # Or with string (will be validated and converted)
        >>> endpoint = Endpoint("GET", "/{id}")
    """

    method: HTTPMethod | str  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Validate and convert method, then normalize path."""
        # Convert string to HTTPMethod enum if needed
        if isinstance(self.method, str):
            try:
                self.method = HTTPMethod(self.method)
            except ValueError:
                raise ValueError(
                    f"Invalid HTTP method: {self.method}. "
                    f"Must be one of {list(HTTPMethod)}"
                ) from None

        # Call parent's __post_init__ for path normalization
        super().__post_init__()


@dataclass
class GET(BaseEndpoint):
    """
    GET endpoint for retrieving resources.

    Example:
        >>> from pydantic import BaseModel
        >>> from pydantic_httpx import BaseResource, Endpoint, GET
        >>>
        >>> class User(BaseModel):
        >>>     id: int
        >>>     name: str
        >>>
        >>> class UserResource(BaseResource):
        >>>     get: Endpoint[User] = GET("/{id}")
        >>>     list_all: Endpoint[list[User]] = GET("")
    """

    def __init__(
        self,
        path: str,
        query_model: type[BaseModel] | None = None,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth: httpx.Auth | tuple[str, str] | str | None = None,
        follow_redirects: bool | None = None,
    ) -> None:
        super().__init__(
            method=HTTPMethod.GET,
            path=path,
            query_model=query_model,
            timeout=timeout,
            headers=headers or {},
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
        )


@dataclass
class POST(BaseEndpoint):
    """
    POST endpoint for creating resources.

    Example:
        >>> create: Endpoint[User] = POST("")
    """

    def __init__(
        self,
        path: str,
        query_model: type[BaseModel] | None = None,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth: httpx.Auth | tuple[str, str] | str | None = None,
        follow_redirects: bool | None = None,
    ) -> None:
        super().__init__(
            method=HTTPMethod.POST,
            path=path,
            query_model=query_model,
            timeout=timeout,
            headers=headers or {},
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
        )


@dataclass
class PUT(BaseEndpoint):
    """
    PUT endpoint for updating/replacing resources.

    Example:
        >>> update: Endpoint[User] = PUT("/{id}")
    """

    def __init__(
        self,
        path: str,
        query_model: type[BaseModel] | None = None,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth: httpx.Auth | tuple[str, str] | str | None = None,
        follow_redirects: bool | None = None,
    ) -> None:
        super().__init__(
            method=HTTPMethod.PUT,
            path=path,
            query_model=query_model,
            timeout=timeout,
            headers=headers or {},
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
        )


@dataclass
class PATCH(BaseEndpoint):
    """
    PATCH endpoint for partially updating resources.

    Example:
        >>> partial_update: Endpoint[User] = PATCH("/{id}")
    """

    def __init__(
        self,
        path: str,
        query_model: type[BaseModel] | None = None,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth: httpx.Auth | tuple[str, str] | str | None = None,
        follow_redirects: bool | None = None,
    ) -> None:
        super().__init__(
            method=HTTPMethod.PATCH,
            path=path,
            query_model=query_model,
            timeout=timeout,
            headers=headers or {},
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
        )


@dataclass
class DELETE(BaseEndpoint):
    """
    DELETE endpoint for removing resources.

    Example:
        >>> delete: Endpoint[None] = DELETE("/{id}")
    """

    def __init__(
        self,
        path: str,
        query_model: type[BaseModel] | None = None,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth: httpx.Auth | tuple[str, str] | str | None = None,
        follow_redirects: bool | None = None,
    ) -> None:
        super().__init__(
            method=HTTPMethod.DELETE,
            path=path,
            query_model=query_model,
            timeout=timeout,
            headers=headers or {},
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
        )


@dataclass
class HEAD(BaseEndpoint):
    """
    HEAD endpoint for retrieving headers only.

    Example:
        >>> check: Endpoint[None] = HEAD("/{id}")
    """

    def __init__(
        self,
        path: str,
        query_model: type[BaseModel] | None = None,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth: httpx.Auth | tuple[str, str] | str | None = None,
        follow_redirects: bool | None = None,
    ) -> None:
        super().__init__(
            method=HTTPMethod.HEAD,
            path=path,
            query_model=query_model,
            timeout=timeout,
            headers=headers or {},
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
        )


@dataclass
class OPTIONS(BaseEndpoint):
    """
    OPTIONS endpoint for retrieving supported methods.

    Example:
        >>> options: Endpoint[dict] = OPTIONS("")
    """

    def __init__(
        self,
        path: str,
        query_model: type[BaseModel] | None = None,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth: httpx.Auth | tuple[str, str] | str | None = None,
        follow_redirects: bool | None = None,
    ) -> None:
        super().__init__(
            method=HTTPMethod.OPTIONS,
            path=path,
            query_model=query_model,
            timeout=timeout,
            headers=headers or {},
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
        )
