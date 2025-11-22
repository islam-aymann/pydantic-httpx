"""Base HTTP client with Pydantic validation."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from typing_extensions import TypeVar, get_args, get_origin, get_type_hints

from pydantic_httpx.config import ClientConfig
from pydantic_httpx.endpoint import BaseEndpoint
from pydantic_httpx.exceptions import HTTPError, RequestError, ValidationError
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

    Supports two endpoint types:
    - Endpoint[T]: Returns data only (auto-extracts response.data)
    - ResponseEndpoint[T]: Returns full DataResponse[T] wrapper

    Attributes:
        client_config: Configuration for the HTTP client.
        _is_async_client: Class-level flag indicating this is a sync client.

    Example:
        >>> from pydantic import BaseModel
        >>> from pydantic_httpx import (
        >>>     Client, BaseResource, ClientConfig, GET, Endpoint
        >>> )
        >>>
        >>> class User(BaseModel):
        >>>     id: int
        >>>     name: str
        >>>
        >>> class UserResource(BaseResource):
        >>>     resource_config = ResourceConfig(prefix="/users")
        >>>     get: Endpoint[User] = GET("/{id}")
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
    _endpoint_info: dict[str, tuple[BaseEndpoint, type[Any], bool]]

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

        # Handle client_config - ensure it's a dict and apply defaults
        if not hasattr(cls, "client_config"):
            cls.client_config = {}
        elif cls.client_config is None:
            cls.client_config = {}

        # Apply defaults to client_config
        config_defaults: ClientConfig = {
            "base_url": "",
            "timeout": 30.0,
            "headers": {},
            "params": {},
            "follow_redirects": True,
            "max_redirects": 20,
            "verify": True,
            "cert": None,
            "http2": False,
            "proxies": {},
            "raise_on_error": True,
            "validate_response": True,
            "auth": None,
        }
        # Merge user config over defaults
        cls.client_config = {**config_defaults, **cls.client_config}

        # Use get_type_hints to properly resolve forward references and generics
        try:
            type_hints = get_type_hints(cls, include_extras=True)
        except Exception:
            # Fallback to raw annotations if get_type_hints fails
            type_hints = getattr(cls, "__annotations__", {})

        for attr_name, annotation in type_hints.items():
            # Check if it's a BaseResource subclass
            if isinstance(annotation, type) and issubclass(annotation, BaseResource):
                # Store the resource class for later initialization
                if not hasattr(cls, "_resource_classes"):
                    cls._resource_classes = {}
                cls._resource_classes[attr_name] = annotation
                continue

            # Check if it's a direct endpoint definition on the client
            endpoint = getattr(cls, attr_name, None)
            if isinstance(endpoint, BaseEndpoint):
                # Detect if this is Endpoint[T] or ResponseEndpoint[T]
                origin = get_origin(annotation)
                return_data_only = True  # Default to Endpoint[T] behavior

                if origin is not None:
                    origin_name = getattr(origin, "__name__", "")
                    if origin_name == "ResponseEndpoint":
                        return_data_only = False

                # Create and set the descriptor (same as Resource does)
                # Note: validators will be retrieved at runtime from client instance
                descriptor = EndpointDescriptor(
                    attr_name, endpoint, annotation, return_data_only
                )
                setattr(cls, attr_name, descriptor)

    def _init_resources(self) -> None:
        """Initialize resource instances and bind them to this client."""
        resource_classes = getattr(self.__class__, "_resource_classes", {})

        for attr_name, resource_class in resource_classes.items():
            # Create resource instance bound to this client
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
            # Extract the inner type from DataResponse[T]
            inner_type = self._extract_response_model(response_type)

            # Merge endpoint headers with config headers
            headers = {**self.client_config["headers"], **endpoint.headers}

            # Determine timeout (endpoint-specific or client default)
            timeout = endpoint.timeout or self.client_config["timeout"]

            # Build request parameters
            request_params: dict[str, Any] = {"headers": headers, "timeout": timeout}

            # Add cookies if provided
            if endpoint.cookies is not None:
                request_params["cookies"] = endpoint.cookies

            # Add auth if provided
            if endpoint.auth is not None:
                request_params["auth"] = endpoint.auth

            # Add follow_redirects if provided
            if endpoint.follow_redirects is not None:
                request_params["follow_redirects"] = endpoint.follow_redirects

            # Convert method to string early (needed for error handling)
            method_str = method.value if isinstance(method, HTTPMethod) else method

            # Handle request body with optional validation
            if "json" in kwargs:
                json_data = kwargs["json"]
                # Validate request body if model provided
                if request_model is not None:
                    try:
                        validated_request = request_model(**json_data)
                        request_params["json"] = validated_request.model_dump()
                    except PydanticValidationError as e:
                        # Create a dummy response for ValidationError
                        dummy_response = httpx.Response(
                            status_code=400,
                            request=httpx.Request(method_str, path),
                        )
                        raise ValidationError(
                            "Request validation failed",
                            dummy_response,
                            e.errors(),
                            raw_data=json_data,
                        ) from e
                else:
                    request_params["json"] = json_data

            # Handle query parameters (exclude 'json' since it's for body)
            query_kwargs = {k: v for k, v in kwargs.items() if k != "json"}
            if endpoint.query_model and query_kwargs:
                # Validate query params if model provided
                query_data = endpoint.query_model(**query_kwargs)
                request_params["params"] = query_data.model_dump()
            elif query_kwargs:
                # Pass remaining kwargs as query params
                request_params["params"] = query_kwargs

            # Execute HTTP request
            response = self._httpx_client.request(method_str, path, **request_params)

            # Check for HTTP errors if configured
            if self.client_config["raise_on_error"] and response.is_error:
                raise HTTPError(response)

            # Validate and parse response
            validated_data = self._validate_response(response, inner_type)

            return DataResponse(response, validated_data)

        except httpx.TimeoutException as e:
            raise RequestError(f"Request timeout: {e}", original_exception=e) from e
        except httpx.RequestError as e:
            raise RequestError(f"Request failed: {e}", original_exception=e) from e

    def _extract_response_model(self, response_type: type) -> Any:
        """
        Extract the inner type from DataResponse[T].

        Args:
            response_type: The full response type (e.g., DataResponse[User]).

        Returns:
            The inner type T.
        """
        args = get_args(response_type)
        if args:
            return args[0]
        return response_type

    def _validate_response(self, response: httpx.Response, model: type) -> Any:
        """
        Validate response data against a Pydantic model.

        Args:
            response: The httpx response.
            model: The Pydantic model to validate against.

        Returns:
            Validated data (model instance, list of models, dict, or None).

        Raises:
            ValidationError: If validation fails.
        """
        # Handle None responses (e.g., DELETE with 204)
        if model is type(None) or response.status_code == 204:
            return None

        data = None
        try:
            # Parse JSON response
            data = response.json()

            # Check if the model is a generic type (e.g., list[User])
            origin = get_origin(model)

            # Handle list of models
            if origin is list:
                # Extract item type from list[T]
                item_type = get_args(model)[0] if get_args(model) else dict
                if isinstance(item_type, type) and issubclass(item_type, BaseModel):
                    return [item_type(**item) for item in data]
                return data

            # Handle single Pydantic model
            if isinstance(model, type) and issubclass(model, BaseModel):
                return model(**data)

            # Return raw data for dict or other types
            return data

        except PydanticValidationError as e:
            raise ValidationError(
                "Response validation failed",
                response,
                e.errors(),
                raw_data=data,
            ) from e
        except Exception as e:
            raise RequestError(
                f"Failed to parse response: {e}", original_exception=e
            ) from e

    def __enter__(self) -> Client:
        """Support context manager protocol."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Close client when exiting context."""
        self.close()

    def close(self) -> None:
        """Close the underlying httpx client."""
        self._httpx_client.close()
