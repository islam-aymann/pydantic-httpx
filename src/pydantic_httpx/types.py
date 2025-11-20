"""Type definitions and protocols for pydantic-httpx."""

from enum import Enum
from typing import Any, TypeAlias

from pydantic import BaseModel


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
