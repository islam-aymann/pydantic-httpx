"""Base resource class for defining HTTP endpoints."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, TypeVar, get_type_hints, overload

from pydantic_httpx.config import ResourceConfig
from pydantic_httpx.endpoint import BaseEndpoint
from pydantic_httpx.response import DataResponse

if TYPE_CHECKING:
    from pydantic_httpx.async_client import AsyncBaseClient
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

    def __set_name__(self, owner: type, name: str) -> None:
        """Called when the descriptor is assigned to a class attribute."""
        self.name = name

    def __call__(self, **kwargs: Any) -> DataResponse[Any]:
        """
        Type hint for IDE support indicating this descriptor is callable.

        This method is never actually called at runtime - it exists purely
        for type checkers and IDEs to understand that accessing this descriptor
        on an instance returns a callable that produces DataResponse[T].

        The actual implementation is in __get__ which returns a function.

        Args:
            **kwargs: Path parameters, query parameters, or request body data.

        Returns:
            DataResponse[T]: Response wrapper containing validated data.

        Raises:
            NotImplementedError: This method should never be called at runtime.
        """
        raise NotImplementedError(
            "EndpointDescriptor.__call__ should never be invoked directly. "
            "This method exists only for type checking. The actual callable "
            "is returned by __get__."
        )

    @overload
    def __get__(
        self, instance: None, owner: type[BaseResource]
    ) -> EndpointDescriptor: ...

    @overload
    def __get__(
        self, instance: BaseResource, owner: type[BaseResource]
    ) -> Callable[..., DataResponse[Any] | Awaitable[DataResponse[Any]]]: ...

    def __get__(
        self, instance: BaseResource | None, owner: type[BaseResource]
    ) -> (
        EndpointDescriptor
        | Callable[..., DataResponse[Any] | Awaitable[DataResponse[Any]]]
    ):
        """
        Return a callable that executes the HTTP request.

        Returns either a sync or async function based on the client type.

        Args:
            instance: The resource instance (or None if accessed from class).
            owner: The resource class.

        Returns:
            A callable that executes the endpoint when called.
            Returns sync function for BaseClient, async function for AsyncBaseClient.
        """
        if instance is None:
            # Accessed from class, return descriptor itself
            return self

        # Check client type using the _is_async_client flag
        if instance._client and getattr(instance._client, "_is_async_client", False):
            # Return async method for async clients
            async def async_endpoint_method(**kwargs: Any) -> DataResponse[Any]:
                if instance._client is None:
                    raise RuntimeError(
                        f"Resource '{owner.__name__}' is not bound to a client. "
                        f"Make sure the resource is properly initialized on a client."
                    )

                # Get the full path (prefix + endpoint path)
                prefix = instance.resource_config.prefix

                # Format path with parameters
                path_params = {
                    k: v
                    for k, v in kwargs.items()
                    if k in self.endpoint.get_path_params()
                }
                formatted_path = self.endpoint.format_path(**path_params)
                full_path = f"{prefix}{formatted_path}".rstrip("/") or "/"

                # Remaining kwargs are query/body params (handled by client)
                non_path_params = {
                    k: v for k, v in kwargs.items() if k not in path_params
                }

                # Execute async request via client
                return await instance._client._execute_request(  # type: ignore[union-attr]
                    method=self.endpoint.method,
                    path=full_path,
                    response_type=self.response_type,
                    endpoint=self.endpoint,
                    **non_path_params,
                )

            return async_endpoint_method
        else:
            # Return sync method for sync clients
            def sync_endpoint_method(**kwargs: Any) -> DataResponse[Any]:
                if instance._client is None:
                    raise RuntimeError(
                        f"Resource '{owner.__name__}' is not bound to a client. "
                        f"Make sure the resource is properly initialized on a client."
                    )

                # Get the full path (prefix + endpoint path)
                prefix = instance.resource_config.prefix

                # Format path with parameters
                path_params = {
                    k: v
                    for k, v in kwargs.items()
                    if k in self.endpoint.get_path_params()
                }
                formatted_path = self.endpoint.format_path(**path_params)
                full_path = f"{prefix}{formatted_path}".rstrip("/") or "/"

                # Remaining kwargs are query/body params (handled by client)
                non_path_params = {
                    k: v for k, v in kwargs.items() if k not in path_params
                }

                # Execute sync request via client
                return instance._client._execute_request(  # type: ignore[return-value]
                    method=self.endpoint.method,
                    path=full_path,
                    response_type=self.response_type,
                    endpoint=self.endpoint,
                    **non_path_params,
                )

            return sync_endpoint_method


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
        >>>     BaseResource, GET, POST, EndpointMethod, ResourceConfig
        >>> )
        >>>
        >>> class User(BaseModel):
        >>>     id: int
        >>>     name: str
        >>>
        >>> class UserResource(BaseResource):
        >>>     resource_config = ResourceConfig(prefix="/users")
        >>>
        >>>     get: EndpointMethod[User] = GET("/{id}")
        >>>     list: EndpointMethod[list[User]] = GET("")
        >>>     create: EndpointMethod[User] = POST("", request_model=User)
    """

    resource_config: ResourceConfig = ResourceConfig()

    def __init__(self, client: BaseClient | AsyncBaseClient | None = None) -> None:
        """
        Initialize the resource.

        Args:
            client: The client instance this resource is bound to (sync or async).
        """
        self._client = client

    def __init_subclass__(cls) -> None:
        """
        Called when a subclass is created.

        This method parses endpoint definitions and replaces them with
        EndpointDescriptor instances.

        Supports: get: EndpointMethod[User] = GET("/{id}")
        """
        super().__init_subclass__()

        # Use get_type_hints to properly resolve forward references and generics
        try:
            type_hints = get_type_hints(cls, include_extras=True)
        except Exception:
            # Fallback to raw annotations if get_type_hints fails
            type_hints = getattr(cls, "__annotations__", {})

        for attr_name, annotation in type_hints.items():
            # Get the actual value assigned to this attribute
            endpoint = getattr(cls, attr_name, None)

            # Skip if not a BaseEndpoint instance (includes all endpoint types)
            if not isinstance(endpoint, BaseEndpoint):
                continue

            # The annotation should be EndpointMethod[T] (or DataResponse[T] for compat)
            # The annotation itself is the response type wrapper
            response_type = annotation

            # Create and set the descriptor
            descriptor = EndpointDescriptor(attr_name, endpoint, response_type)
            setattr(cls, attr_name, descriptor)
