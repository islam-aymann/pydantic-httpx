"""Integration library for HTTPX with Pydantic models."""

__version__ = "0.1.0"

from pydantic_httpx.config import ClientConfig, ResourceConfig
from pydantic_httpx.exceptions import (
    HTTPError,
    RequestError,
    RequestTimeoutError,
    ResponseError,
    ValidationError,
)
from pydantic_httpx.response import DataResponse

__all__ = [
    "__version__",
    # Config
    "ClientConfig",
    "ResourceConfig",
    # Exceptions
    "ResponseError",
    "HTTPError",
    "ValidationError",
    "RequestTimeoutError",
    "RequestError",
    # Response
    "DataResponse",
]
