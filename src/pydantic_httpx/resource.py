"""Base resource class for defining HTTP endpoints."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, overload

from typing_extensions import TypeVar, get_args, get_origin, get_type_hints

from pydantic_httpx._defaults import RESOURCE_CONFIG_DEFAULTS
from pydantic_httpx.config import ResourceConfig
from pydantic_httpx.endpoint import BaseEndpoint
from pydantic_httpx.response import DataResponse
from pydantic_httpx.validators import (
    apply_after_validators,
    apply_before_validators,
    apply_wrap_validator,
    get_validators,
)

if TYPE_CHECKING:
    from pydantic_httpx.async_client import AsyncClient
    from pydantic_httpx.client import Client

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
        request_model: type | None = None,
    ) -> None:
        """
        Initialize endpoint descriptor.

        Args:
            name: The attribute name of the endpoint.
            endpoint: The BaseEndpoint metadata.
            response_type: Expected response type (Endpoint[T]).
            request_model: Optional Pydantic model for request validation.
        """
        self.name = name
        self.endpoint = endpoint
        self.response_type = response_type
        self.request_model = request_model

    def __set_name__(self, owner: type, name: str) -> None:
        """
        Called when the descriptor is assigned to a class attribute.
        """
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
    def __get__(self, instance: None, owner: type) -> EndpointDescriptor: ...

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
            resource_config = getattr(instance, "resource_config", {})
            prefix = resource_config.get("prefix", "") if resource_config else ""
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
                        f"Endpoint '{self.name}' on '{owner.__name__}' "
                        f"is not bound to a client. "
                        f"Make sure it is properly initialized."
                    )

                # Get validators for this endpoint from resource or client
                # Resource validators take precedence
                validators = getattr(instance, "_validators", {}).get(self.name, [])
                if not validators:
                    validators = getattr(client, "_validators", {}).get(self.name, [])

                # Separate validators by mode
                before_validators = [v for v in validators if v.mode == "before"]
                after_validators = [v for v in validators if v.mode == "after"]
                wrap_validators = [v for v in validators if v.mode == "wrap"]

                # Apply "before" validators to transform parameters
                params = kwargs
                if before_validators:
                    params = apply_before_validators(
                        before_validators, params, instance
                    )

                # Define handler for wrap validators
                async def handler(params: dict[str, Any]) -> DataResponse[Any]:
                    # Format path with parameters
                    path_params = {
                        k: v
                        for k, v in params.items()
                        if k in self.endpoint.get_path_params()
                    }
                    formatted_path = self.endpoint.format_path(**path_params)
                    full_path = f"{prefix}{formatted_path}".rstrip("/") or "/"

                    # Remaining kwargs are query/body params (handled by client)
                    non_path_params = {
                        k: v for k, v in params.items() if k not in path_params
                    }

                    # Execute async request via client
                    result = await client._execute_request(
                        method=self.endpoint.method,
                        path=full_path,
                        response_type=self.response_type,
                        endpoint=self.endpoint,
                        request_model=self.request_model,
                        **non_path_params,
                    )
                    return result  # type: ignore[no-any-return]

                # Apply "wrap" validators (if any)
                if wrap_validators:
                    # Apply wrap validators (they control the execution)
                    # For async, we need to make handler that wrap can call
                    async def wrapped_handler(p: dict[str, Any]) -> DataResponse[Any]:
                        return await handler(p)

                    # Only first wrap validator (multiple wraps not supported)
                    result = apply_wrap_validator(
                        wrap_validators[0],
                        wrapped_handler,  # type: ignore[arg-type]
                        params,
                        instance,
                    )
                    # If wrap validator returns awaitable, await it
                    if hasattr(result, "__await__"):
                        result = await result
                    if isinstance(result, DataResponse):
                        response = result
                    else:
                        response = DataResponse(None, result)  # type: ignore[arg-type]
                else:
                    # No wrap validators, execute normally
                    response = await handler(params)

                # Apply "after" validators to transform response
                result = response
                if after_validators:
                    result = apply_after_validators(
                        after_validators, response, instance
                    )

                # Always return full DataResponse[T]
                return result if isinstance(result, DataResponse) else response

            return async_endpoint_method
        else:
            # Return sync method for sync clients
            def sync_endpoint_method(**kwargs: Any) -> DataResponse[Any]:
                if client is None:
                    raise RuntimeError(
                        f"Endpoint '{self.name}' on '{owner.__name__}' "
                        f"is not bound to a client. "
                        f"Make sure it is properly initialized."
                    )

                # Get validators for this endpoint from resource or client
                # Resource validators take precedence
                validators = getattr(instance, "_validators", {}).get(self.name, [])
                if not validators:
                    validators = getattr(client, "_validators", {}).get(self.name, [])

                # Separate validators by mode
                before_validators = [v for v in validators if v.mode == "before"]
                after_validators = [v for v in validators if v.mode == "after"]
                wrap_validators = [v for v in validators if v.mode == "wrap"]

                # Apply "before" validators to transform parameters
                params = kwargs
                if before_validators:
                    params = apply_before_validators(
                        before_validators, params, instance
                    )

                # Define handler for wrap validators
                def handler(params: dict[str, Any]) -> DataResponse[Any]:
                    # Format path with parameters
                    path_params = {
                        k: v
                        for k, v in params.items()
                        if k in self.endpoint.get_path_params()
                    }
                    formatted_path = self.endpoint.format_path(**path_params)
                    full_path = f"{prefix}{formatted_path}".rstrip("/") or "/"

                    # Remaining kwargs are query/body params (handled by client)
                    non_path_params = {
                        k: v for k, v in params.items() if k not in path_params
                    }

                    # Execute sync request via client
                    result = client._execute_request(
                        method=self.endpoint.method,
                        path=full_path,
                        response_type=self.response_type,
                        endpoint=self.endpoint,
                        request_model=self.request_model,
                        **non_path_params,
                    )
                    return result  # type: ignore[no-any-return]

                # Apply "wrap" validators (if any)
                if wrap_validators:
                    # Apply wrap validators (they control the execution)
                    # Only first wrap validator (multiple wraps not supported)
                    result = apply_wrap_validator(
                        wrap_validators[0], handler, params, instance
                    )
                    if isinstance(result, DataResponse):
                        response = result
                    else:
                        response = DataResponse(None, result)  # type: ignore[arg-type]
                else:
                    # No wrap validators, execute normally
                    response = handler(params)

                # Apply "after" validators to transform response
                result = response
                if after_validators:
                    result = apply_after_validators(
                        after_validators, response, instance
                    )

                # Always return full DataResponse[T]
                return result if isinstance(result, DataResponse) else response

            return sync_endpoint_method


class BaseResource:
    """
    Base class for defining HTTP resource endpoints.

    Resources group related endpoints together with a common prefix.
    Supports both Annotated and assignment syntax for endpoint definitions.

    Attributes:
        resource_config: Configuration for the resource (prefix, timeout, headers).

    Example (Annotated syntax - recommended):
        >>> from typing import Annotated
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
        >>>     get: Annotated[Endpoint[User], GET("/{id}")]
        >>>     list: Annotated[Endpoint[list[User]], GET("")]
        >>>     create: Annotated[Endpoint[User, User], POST("")]

    Example (Assignment syntax - alternative):
        >>> class UserResource(BaseResource):
        >>>     resource_config = ResourceConfig(prefix="/users")
        >>>
        >>>     get: Endpoint[User] = GET("/{id}")
        >>>     list: Endpoint[list[User]] = GET("")
        >>>     create: Endpoint[User, User] = POST("")
    """

    resource_config: ResourceConfig = {}

    def __init__(self, client: Client | AsyncClient | None = None) -> None:
        """
        Initialize the resource.

        Args:
            client: The client instance this resource is bound to (sync or async).
        """
        self._client = client
        # Extract validators for this resource class
        self._validators = get_validators(self.__class__)

    def __init_subclass__(cls) -> None:
        """
        Called when a subclass is created.

        This method parses endpoint definitions and replaces them with
        EndpointDescriptor instances.

        Supports two syntaxes:
        1. Annotated: get: Annotated[Endpoint[User], GET("/{id}")]
        2. Assignment: get: Endpoint[User] = GET("/{id}")

        Both syntaxes provide identical type inference and runtime behavior.
        """
        super().__init_subclass__()

        if not hasattr(cls, "resource_config") or cls.resource_config is None:
            cls.resource_config = {}

        cls.resource_config = {**RESOURCE_CONFIG_DEFAULTS, **cls.resource_config}

        try:
            type_hints = get_type_hints(cls, include_extras=True)
        except Exception:
            type_hints = getattr(cls, "__annotations__", {})

        for attr_name, annotation in type_hints.items():
            endpoint_spec = None
            endpoint_protocol = None
            request_model = None

            origin = get_origin(annotation)
            if origin is not None:
                origin_name = getattr(origin, "__name__", "")
                if origin_name == "Annotated":
                    args = get_args(annotation)
                    if args and len(args) >= 2:
                        endpoint_protocol = args[0]
                        metadata = args[1:]

                        for item in metadata:
                            if isinstance(item, BaseEndpoint):
                                endpoint_spec = item
                                break

            if endpoint_spec is None:
                attr_value = getattr(cls, attr_name, None)
                if isinstance(attr_value, BaseEndpoint):
                    endpoint_spec = attr_value
                    endpoint_protocol = annotation

            if endpoint_spec is not None and endpoint_protocol is not None:
                protocol_origin = get_origin(endpoint_protocol)
                if protocol_origin is not None:
                    protocol_args = get_args(endpoint_protocol)
                    if len(protocol_args) > 1 and protocol_args[1] is not type(None):
                        request_model = protocol_args[1]

                response_type = endpoint_protocol

                descriptor = EndpointDescriptor(
                    attr_name, endpoint_spec, response_type, request_model
                )
                setattr(cls, attr_name, descriptor)
                descriptor.__set_name__(cls, attr_name)
