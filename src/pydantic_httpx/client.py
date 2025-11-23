"""Base HTTP client with Pydantic validation."""

from __future__ import annotations

from typing import Any

import httpx
from typing_extensions import TypeVar, get_args, get_origin, get_type_hints

from pydantic_httpx._defaults import CLIENT_CONFIG_DEFAULTS
from pydantic_httpx._request_builder import (
    add_query_params,
    build_request_params,
    convert_method_to_string,
    validate_and_add_body_params,
)
from pydantic_httpx._response_validator import extract_response_model, validate_response
from pydantic_httpx.config import ClientConfig
from pydantic_httpx.endpoint import BaseEndpoint
from pydantic_httpx.exceptions import HTTPError, RequestError
from pydantic_httpx.resource import BaseResource, EndpointDescriptor
from pydantic_httpx.response import DataResponse
from pydantic_httpx.types import HTTPMethod
from pydantic_httpx.validators import get_validators

T = TypeVar("T")


class Client:
    """
    HTTP client that integrates httpx with Pydantic models.

    This client wraps httpx.Client and provides automatic request/response
    validation using Pydantic models defined in resource classes.

    All endpoints use Endpoint[T] which returns DataResponse[T] wrapper.
    Access the validated data using response.data property.

    Attributes:
        client_config: Configuration for the HTTP client.
        _is_async_client: Class-level flag indicating this is a sync client.

    Example:
        >>> from typing import Annotated
        >>> from pydantic import BaseModel
        >>> from pydantic_httpx import (
        >>>     Client, BaseResource, ClientConfig, GET, Endpoint, ResourceConfig
        >>> )
        >>>
        >>> class User(BaseModel):
        >>>     id: int
        >>>     name: str
        >>>
        >>> class UserResource(BaseResource):
        >>>     resource_config = ResourceConfig(prefix="/users")
        >>>     get: Annotated[Endpoint[User], GET("/{id}")]
        >>>
        >>> class APIClient(Client):
        >>>     client_config = ClientConfig(base_url="https://api.example.com")
        >>>     users: UserResource
        >>>
        >>> client = APIClient()
        >>> user = client.users.get(id=1)  # Returns User directly
    """

    client_config: ClientConfig = {}
    _is_async_client: bool = False
    _resource_classes: dict[str, type[BaseResource]]

    def __init__(self) -> None:
        """Initialize the client and bind resources."""
        # Create httpx client
        self._httpx_client = httpx.Client(
            base_url=self.client_config["base_url"],
            timeout=self.client_config["timeout"],
            headers=self.client_config["headers"],
            follow_redirects=self.client_config["follow_redirects"],
        )

        # Extract and store validators for this client
        self._validators = get_validators(self.__class__)

        # Initialize and bind resources
        self._init_resources()

    def __init_subclass__(cls) -> None:
        """Called when a subclass is created to parse resources and endpoints."""
        super().__init_subclass__()

        if not hasattr(cls, "client_config") or cls.client_config is None:
            cls.client_config = {}

        cls.client_config = {**CLIENT_CONFIG_DEFAULTS, **cls.client_config}

        try:
            type_hints = get_type_hints(cls, include_extras=True)
        except Exception:
            type_hints = getattr(cls, "__annotations__", {})

        for attr_name, annotation in type_hints.items():
            if isinstance(annotation, type) and issubclass(annotation, BaseResource):
                if not hasattr(cls, "_resource_classes"):
                    cls._resource_classes = {}
                cls._resource_classes[attr_name] = annotation
                continue

            origin = get_origin(annotation)

            if origin is None:
                continue

            origin_name = getattr(origin, "__name__", "")
            if origin_name != "Annotated":
                continue

            args = get_args(annotation)
            if not args or len(args) < 2:
                continue

            endpoint_protocol = args[0]
            metadata = args[1:]

            endpoint_spec = None
            for item in metadata:
                if isinstance(item, BaseEndpoint):
                    endpoint_spec = item
                    break

            if endpoint_spec is None:
                continue

            protocol_args = get_args(endpoint_protocol)
            request_model = None
            if len(protocol_args) > 1 and protocol_args[1] is not type(None):
                request_model = protocol_args[1]

            descriptor = EndpointDescriptor(
                attr_name,
                endpoint_spec,
                endpoint_protocol,
                request_model,
            )
            setattr(cls, attr_name, descriptor)
            descriptor.__set_name__(cls, attr_name)

    def _init_resources(self) -> None:
        """Initialize resource instances and bind them to this client."""
        resource_classes = getattr(self.__class__, "_resource_classes", {})

        for attr_name, resource_class in resource_classes.items():
            resource_instance = resource_class(client=self)
            setattr(self, attr_name, resource_instance)

    def _execute_request(
        self,
        method: HTTPMethod | str,
        path: str,
        response_type: type,
        endpoint: BaseEndpoint,
        request_model: type | None = None,
        **kwargs: Any,
    ) -> DataResponse[Any]:
        """
        Execute an HTTP request and validate the response.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: Full request path.
            response_type: Expected response type (DataResponse[T]).
            endpoint: BaseEndpoint metadata.
            request_model: Optional Pydantic model for request validation.
            **kwargs: Request parameters (query params, body, etc.).

        Returns:
            DataResponse with validated data.

        Raises:
            HTTPError: If response status code indicates an error.
            ValidationError: If response validation fails.
            RequestError: If the request fails to execute.
        """
        try:
            inner_type = extract_response_model(response_type)
            method_str = convert_method_to_string(method)

            request_params = build_request_params(
                endpoint, self.client_config, kwargs, request_model
            )
            validate_and_add_body_params(
                request_params, kwargs, request_model, method_str, path
            )
            add_query_params(request_params, kwargs, endpoint)

            response = self._httpx_client.request(method_str, path, **request_params)

            if self.client_config["raise_on_error"] and response.is_error:
                raise HTTPError(response)

            validated_data = validate_response(response, inner_type)
            return DataResponse(response, validated_data)

        except httpx.TimeoutException as e:
            raise RequestError(f"Request timeout: {e}", original_exception=e) from e
        except httpx.RequestError as e:
            raise RequestError(f"Request failed: {e}", original_exception=e) from e

    def __enter__(self) -> Client:
        """Support context manager protocol."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Close client when exiting context."""
        self.close()

    def close(self) -> None:
        """Close the underlying httpx client."""
        self._httpx_client.close()
