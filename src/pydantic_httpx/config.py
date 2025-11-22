"""Configuration TypedDicts for clients and resources."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, TypedDict

if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired

if TYPE_CHECKING:
    import httpx


class ClientConfig(TypedDict, total=False):
    """
    Configuration for Client.

    Similar to Pydantic's ConfigDict - a TypedDict that provides editor support.
    All fields are optional.

    Example:
        >>> # Recommended: Use constructor for full editor support (autocomplete)
        >>> class APIClient(Client):
        >>>     client_config = ClientConfig(
        >>>         base_url="https://api.example.com",
        >>>         timeout=30.0,
        >>>     )
        >>>
        >>> # Alternative: Dict literal with type hint
        >>> class APIClient(Client):
        >>>     client_config: ClientConfig = {
        >>>         "base_url": "https://api.example.com",
        >>>     }
    """

    base_url: str
    timeout: float
    headers: dict[str, str]
    params: dict[str, Any]
    follow_redirects: bool
    max_redirects: int
    verify: bool
    cert: NotRequired[str | tuple[str, str] | None]
    http2: bool
    proxies: dict[str, str]
    raise_on_error: bool
    validate_response: bool
    auth: NotRequired[httpx.Auth | None]


class ResourceConfig(TypedDict, total=False):
    """
    Configuration for BaseResource.

    Similar to Pydantic's ConfigDict - a TypedDict that provides editor support.
    All fields are optional.

    Example:
        >>> # Recommended: Use constructor for full editor support (autocomplete)
        >>> class UserResource(BaseResource):
        >>>     resource_config = ResourceConfig(
        >>>         prefix="/users",
        >>>         timeout=60.0,
        >>>     )
        >>>
        >>> # Alternative: Dict literal with type hint
        >>> class UserResource(BaseResource):
        >>>     resource_config: ResourceConfig = {
        >>>         "prefix": "/users",
        >>>     }
    """

    prefix: str
    timeout: NotRequired[float | None]
    headers: dict[str, str]
    validate_response: NotRequired[bool | None]
    raise_on_error: NotRequired[bool | None]
    description: NotRequired[str | None]
    tags: list[str]
