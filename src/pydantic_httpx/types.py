"""Type definitions and protocols for pydantic-httpx."""

from typing import Any, Literal, TypeAlias

from pydantic import BaseModel

# HTTP Methods
HTTPMethod: TypeAlias = Literal[
    "GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"
]

# Request/Response Models
RequestModel: TypeAlias = type[BaseModel] | None
ResponseModel: TypeAlias = (
    type[BaseModel] | type[list[BaseModel]] | type[dict[str, Any]] | type[None]
)

# Common type aliases
Headers: TypeAlias = dict[str, str]
QueryParams: TypeAlias = dict[str, Any]
PathParams: TypeAlias = dict[str, Any]
