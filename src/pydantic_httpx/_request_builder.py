"""Internal module for building HTTP requests with validation.

This module contains shared logic for request parameter handling,
validation, and preparation used by both sync and async clients.
"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import ValidationError as PydanticValidationError

from pydantic_httpx.config import ClientConfig
from pydantic_httpx.endpoint import BaseEndpoint
from pydantic_httpx.exceptions import ValidationError
from pydantic_httpx.types import HTTPMethod

# Body parameter names (mutually exclusive in httpx)
BODY_PARAMS = frozenset({"json", "data", "files", "content"})

# Body parameters that support Pydantic validation
VALIDATED_BODY_PARAMS = frozenset({"json", "data"})

# Body parameters that pass through to httpx without validation
PASSTHROUGH_BODY_PARAMS = frozenset({"files", "content"})


def build_request_params(
    endpoint: BaseEndpoint,
    client_config: ClientConfig,
    kwargs: dict[str, Any],
    request_model: type | None = None,
) -> dict[str, Any]:
    """
    Build httpx request parameters from endpoint config and kwargs.

    Args:
        endpoint: Endpoint metadata with headers, timeout, etc.
        client_config: Client configuration with base settings.
        kwargs: User-provided parameters (path, query, body).
        request_model: Optional Pydantic model for request validation.

    Returns:
        Dictionary of parameters to pass to httpx.request().
    """
    # Start with headers and timeout
    request_params: dict[str, Any] = {
        "headers": {**client_config["headers"], **endpoint.headers},
        "timeout": endpoint.timeout or client_config["timeout"],
    }

    # Add optional endpoint-specific settings
    if endpoint.cookies is not None:
        request_params["cookies"] = endpoint.cookies

    if endpoint.auth is not None:
        request_params["auth"] = endpoint.auth

    if endpoint.follow_redirects is not None:
        request_params["follow_redirects"] = endpoint.follow_redirects

    return request_params


def validate_and_add_body_params(
    request_params: dict[str, Any],
    kwargs: dict[str, Any],
    request_model: type | None,
    method_str: str,
    path: str,
) -> None:
    """
    Validate and add body parameters (json, data, files, content) to request.

    Modifies request_params in place.

    Args:
        request_params: Dictionary to add body parameters to.
        kwargs: User-provided parameters.
        request_model: Optional Pydantic model for validation.
        method_str: HTTP method string (for error messages).
        path: Request path (for error messages).

    Raises:
        ValidationError: If request validation fails.
    """
    # Handle validated body parameters (json, data)
    for param in VALIDATED_BODY_PARAMS:
        if param not in kwargs:
            continue

        body_data = kwargs[param]

        if request_model is not None:
            # Validate with Pydantic model
            try:
                validated_request = request_model(**body_data)
                request_params[param] = validated_request.model_dump()
            except PydanticValidationError as e:
                # Create dummy response for ValidationError
                dummy_response = httpx.Response(
                    status_code=400,
                    request=httpx.Request(method_str, path),
                )
                raise ValidationError(
                    f"Request validation failed for '{param}' parameter",
                    dummy_response,
                    e.errors(),
                    raw_data=body_data,
                ) from e
        else:
            # No validation, pass through
            request_params[param] = body_data

    # Handle pass-through body parameters (files, content)
    for param in PASSTHROUGH_BODY_PARAMS:
        if param in kwargs:
            request_params[param] = kwargs[param]


def add_query_params(
    request_params: dict[str, Any],
    kwargs: dict[str, Any],
    endpoint: BaseEndpoint,
) -> None:
    """
    Add query parameters to request, excluding body parameters.

    Modifies request_params in place.

    Args:
        request_params: Dictionary to add query parameters to.
        kwargs: User-provided parameters.
        endpoint: Endpoint metadata with optional query_model.
    """
    # Extract non-body parameters as query params
    query_kwargs = {k: v for k, v in kwargs.items() if k not in BODY_PARAMS}

    if not query_kwargs:
        return

    if endpoint.query_model:
        # Validate query params with Pydantic model
        query_data = endpoint.query_model(**query_kwargs)
        request_params["params"] = query_data.model_dump()
    else:
        # Pass through without validation
        request_params["params"] = query_kwargs


def convert_method_to_string(method: HTTPMethod | str) -> str:
    """
    Convert HTTPMethod enum to string.

    Args:
        method: HTTP method enum or string.

    Returns:
        Method as string.
    """
    return method.value if isinstance(method, HTTPMethod) else method
