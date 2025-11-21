"""Base resource class for defining HTTP endpoints."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, TypeVar, get_origin, get_type_hints, overload

from pydantic_httpx.config import ResourceConfig
from pydantic_httpx.endpoint import BaseEndpoint
from pydantic_httpx.response import DataResponse

if TYPE_CHECKING:
    from pydantic_httpx.async_client import AsyncBaseClient, AsyncClient
    from pydantic_httpx.client import BaseClient, Client

T = TypeVar("T")


class EndpointDescriptor:
    """
    Descriptor that handles endpoint method calls.

    This descriptor is created for each endpoint defined in a resource
    class and handles the actual HTTP request execution when called.
    """

    def __init__(
        self,
        name: str,
        endpoint: BaseEndpoint,
        response_type: type,
        return_data_only: bool = True,
    ) -> None:
        """
        Initialize endpoint descriptor.

        Args:
            name: The attribute name of the endpoint.
            endpoint: The BaseEndpoint metadata.
            response_type: The expected response type (Endpoint[T] or ResponseEndpoint[T]).
            return_data_only: If True, return data only (Endpoint[T]).
                If False, return full DataResponse[T] (ResponseEndpoint[T]).
        """
        self.name = name
        self.endpoint = endpoint
        self.response_type = response_type
        self.return_data_only = return_data_only

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
        self, instance: None, owner: type
    ) -> EndpointDescriptor: ...

    @overload
    def __get__(
        self, instance: Any, owner: type
    ) -> Callable[..., DataResponse[Any] | Awaitable[DataResponse[Any]]]: ...

    def __get__(
        self, instance: Any, owner: type
    ) -> (
        EndpointDescriptor
        | Callable[..., DataResponse[Any] | Awaitable[DataResponse[Any]]]
    ):
        """
        Return a callable that executes the HTTP request.

        Returns either a sync or async function based on the client type.
        Works with both Resource instances and Client instances.

        Args:
            instance: The resource/client instance (or None if accessed from class).
            owner: The resource/client class.

        Returns:
            A callable that executes the endpoint when called.
            Returns sync function for BaseClient, async function for AsyncBaseClient.
        """
        if instance is None:
            # Accessed from class, return descriptor itself
            return self

        # Determine the client and prefix
        # If instance is a Resource, get client from _client attribute
        # If instance is a Client, use it directly
        if hasattr(instance, "_client"):
            # This is a Resource instance
            client = instance._client
            prefix = getattr(instance, "resource_config", None)
            prefix = prefix.prefix if prefix else ""
        else:
            # This is a Client instance (direct endpoint on client)
            client = instance
            prefix = ""

        # Check client type using the _is_async_client flag
        if client and getattr(client, "_is_async_client", False):
            # Return async method for async clients
            async def async_endpoint_method(**kwargs: Any) -> DataResponse[Any]:
                if client is None:
                    raise RuntimeError(
                        f"Endpoint '{self.name}' on '{owner.__name__}' is not bound to a client. "
                        f"Make sure it is properly initialized."
                    )

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
                response = await client._execute_request(  # type: ignore[union-attr]
                    method=self.endpoint.method,
                    path=full_path,
                    response_type=self.response_type,
                    endpoint=self.endpoint,
                    **non_path_params,
                )

                # Return data only if Endpoint[T], else return full DataResponse[T]
                if self.return_data_only:
                    return response.data
                return response

            return async_endpoint_method
        else:
            # Return sync method for sync clients
            def sync_endpoint_method(**kwargs: Any) -> DataResponse[Any]:
                if client is None:
                    raise RuntimeError(
                        f"Endpoint '{self.name}' on '{owner.__name__}' is not bound to a client. "
                        f"Make sure it is properly initialized."
                    )

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
                response = client._execute_request(  # type: ignore[assignment]
                    method=self.endpoint.method,
                    path=full_path,
                    response_type=self.response_type,
                    endpoint=self.endpoint,
                    **non_path_params,
                )

                # Return data only if Endpoint[T], else return full DataResponse[T]
                if self.return_data_only:
                    return response.data
                return response

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
        >>>     BaseResource, GET, POST, Endpoint, ResourceConfig
        >>> )
        >>>
        >>> class User(BaseModel):
        >>>     id: int
        >>>     name: str
        >>>
        >>> class UserResource(BaseResource):
        >>>     resource_config = ResourceConfig(prefix="/users")
        >>>
        >>>     get: Endpoint[User] = GET("/{id}")
        >>>     list: Endpoint[list[User]] = GET("")
        >>>     create: Endpoint[User] = POST("", request_model=User)
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

        Supports:
        - get: Endpoint[User] = GET("/{id}")  # Returns User
        - get: ResponseEndpoint[User] = GET("/{id}")  # Returns DataResponse[User]
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

            # Detect if this is Endpoint[T] or ResponseEndpoint[T]
            # by checking the __name__ of the Protocol origin
            origin = get_origin(annotation)
            return_data_only = True  # Default to Endpoint[T] behavior

            # Check if annotation is ResponseEndpoint[T]
            if origin is not None:
                origin_name = getattr(origin, "__name__", "")
                if origin_name == "ResponseEndpoint":
                    return_data_only = False

            # The annotation itself is the response type wrapper
            response_type = annotation

            # Create and set the descriptor
            descriptor = EndpointDescriptor(
                attr_name, endpoint, response_type, return_data_only
            )
            setattr(cls, attr_name, descriptor)
