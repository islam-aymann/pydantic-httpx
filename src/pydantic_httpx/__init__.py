"""Integration library for HTTPX with Pydantic models."""

__version__ = "0.3.0"

from pydantic_httpx.async_client import AsyncClient
from pydantic_httpx.client import Client
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
)
from pydantic_httpx.endpoint import Endpoint as EndpointClass
from pydantic_httpx.exceptions import (
    HTTPError,
    RequestError,
    RequestTimeoutError,
    ResponseError,
    ValidationError,
)
from pydantic_httpx.resource import BaseResource
from pydantic_httpx.response import DataResponse
from pydantic_httpx.types import VALID_HTTP_METHODS, Endpoint, HTTPMethod
from pydantic_httpx.validators import endpoint_validator

__all__ = [
    "__version__",
    "ClientConfig",
    "ResourceConfig",
    "ResponseError",
    "HTTPError",
    "ValidationError",
    "RequestTimeoutError",
    "RequestError",
    "DataResponse",
    "Client",
    "AsyncClient",
    "BaseResource",
    "Endpoint",
    "endpoint_validator",
    "BaseEndpoint",
    "EndpointClass",
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "HEAD",
    "OPTIONS",
    "HTTPMethod",
    "VALID_HTTP_METHODS",
]
