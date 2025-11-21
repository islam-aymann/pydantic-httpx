"""Integration library for HTTPX with Pydantic models."""

__version__ = "0.1.0"

from pydantic_httpx.async_client import AsyncBaseClient
from pydantic_httpx.client import BaseClient
from pydantic_httpx.config import ClientConfig, ResourceConfig
from pydantic_httpx.endpoint import (
    DELETE,
    GET,
    HEAD,
    OPTIONS,
    PATCH,
    POST,
    PUT,
    BaseEndpoint,
    Endpoint,
)
from pydantic_httpx.exceptions import (
    HTTPError,
    RequestError,
    RequestTimeoutError,
    ResponseError,
    ValidationError,
)
from pydantic_httpx.resource import BaseResource
from pydantic_httpx.response import DataResponse
from pydantic_httpx.types import (
    VALID_HTTP_METHODS,
    EndpointMethod,
    HTTPMethod,
)

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
    # Client & Resources
    "BaseClient",
    "AsyncBaseClient",
    "BaseResource",
    # Endpoints
    "BaseEndpoint",
    "Endpoint",
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "HEAD",
    "OPTIONS",
    # Types
    "HTTPMethod",
    "VALID_HTTP_METHODS",
    "EndpointMethod",
]
