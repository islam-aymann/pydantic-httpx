"""Integration library for HTTPX with Pydantic models."""

__version__ = "0.1.0"

from pydantic_httpx.config import ClientConfig, ResourceConfig
from pydantic_httpx.exceptions import (
    HTTPError,
    RequestError,
    ResponseError,
    TimeoutError,
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
    "TimeoutError",
    "RequestError",
    # Response
    "DataResponse",
]
