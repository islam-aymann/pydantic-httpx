"""Base resource class for defining HTTP endpoints."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic_httpx.config import ResourceConfig
from pydantic_httpx.endpoint import BaseEndpoint
from pydantic_httpx.response import DataResponse

if TYPE_CHECKING:
    from pydantic_httpx.client import BaseClient

T = TypeVar("T")


class EndpointDescriptor:
    """
    Descriptor that handles endpoint method calls.

    This descriptor is created for each endpoint defined in a resource
    class and handles the actual HTTP request execution when called.
    """

    def __init__(self, name: str, endpoint: BaseEndpoint, response_type: type) -> None:
        """
        Initialize endpoint descriptor.

        Args:
            name: The attribute name of the endpoint.
            endpoint: The BaseEndpoint metadata.
            response_type: The expected response type (DataResponse[T]).
        """
        self.name = name
        self.endpoint = endpoint
        self.response_type = response_type
        self._client: BaseClient | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        """Called when the descriptor is assigned to a class attribute."""
        self.name = name

    def __get__(self, instance: BaseResource | None, owner: type) -> Callable[..., Any]:
        """
        Return a callable that executes the HTTP request.

        Args:
            instance: The resource instance (or None if accessed from class).
            owner: The resource class.

        Returns:
            A callable that executes the endpoint when called.
        """
        if instance is None:
            # Accessed from class, return descriptor itself
            return self  # type: ignore[return-value]

        # Return bound method that will execute the request
        def endpoint_method(**kwargs: Any) -> DataResponse[Any]:
            if instance._client is None:
                raise RuntimeError(
                    f"Resource '{owner.__name__}' is not bound to a client. "
                    f"Make sure the resource is properly initialized on a client."
                )

            # Get the full path (prefix + endpoint path)
            prefix = instance.resource_config.prefix

            # Format path with parameters
            path_params = {
                k: v for k, v in kwargs.items() if k in self.endpoint.get_path_params()
            }
            formatted_path = self.endpoint.format_path(**path_params)
            full_path = f"{prefix}{formatted_path}".rstrip("/") or "/"

            # Remaining kwargs are query/body params (handled by client)
            non_path_params = {k: v for k, v in kwargs.items() if k not in path_params}

            # Execute request via client
            return instance._client._execute_request(
                method=self.endpoint.method,
                path=full_path,
                response_type=self.response_type,
                endpoint=self.endpoint,
                **non_path_params,
            )

        return endpoint_method


class BaseResource:
    """
    Base class for defining HTTP resource endpoints.

    Resources group related endpoints together with a common prefix.
    Endpoints are defined using Annotated type hints with Endpoint metadata.

    Attributes:
        resource_config: Configuration for the resource (prefix, timeout, headers).

    Example:
        >>> from pydantic import BaseModel
        >>> from pydantic_httpx import (
        >>>     BaseResource, GET, POST, DataResponse, ResourceConfig
        >>> )
        >>>
        >>> class User(BaseModel):
        >>>     id: int
        >>>     name: str
        >>>
        >>> class UserResource(BaseResource):
        >>>     resource_config = ResourceConfig(prefix="/users")
        >>>
        >>>     get: DataResponse[User] = GET("/{id}")
        >>>     list: DataResponse[list[User]] = GET("")
        >>>     create: DataResponse[User] = POST("", request_model=User)
    """

    resource_config: ResourceConfig = ResourceConfig()

    def __init__(self, client: BaseClient | None = None) -> None:
        """
        Initialize the resource.

        Args:
            client: The client instance this resource is bound to.
        """
        self._client = client

    def __init_subclass__(cls) -> None:
        """
        Called when a subclass is created.

        This method parses endpoint definitions and replaces them with
        EndpointDescriptor instances.

        Supports: get: DataResponse[User] = GET("/{id}")
        """
        super().__init_subclass__()

        # Parse annotations to find endpoints
        annotations = getattr(cls, "__annotations__", {})

        for attr_name, annotation in annotations.items():
            # Get the actual value assigned to this attribute
            endpoint = getattr(cls, attr_name, None)

            # Skip if not a BaseEndpoint instance (includes all endpoint types)
            if not isinstance(endpoint, BaseEndpoint):
                continue

            # The annotation should be DataResponse[T]
            # Extract the response type from the annotation
            response_type = annotation

            # Create and set the descriptor
            descriptor = EndpointDescriptor(attr_name, endpoint, response_type)
            setattr(cls, attr_name, descriptor)
