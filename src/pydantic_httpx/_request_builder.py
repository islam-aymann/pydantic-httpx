"""Internal module for building HTTP requests with validation."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from pydantic_httpx.config import ClientConfig
from pydantic_httpx.endpoint import BaseEndpoint
from pydantic_httpx.exceptions import ValidationError
from pydantic_httpx.types import HTTPMethod

BODY_PARAMS = frozenset({"json", "data", "files", "content"})
VALIDATED_BODY_PARAMS = frozenset({"json", "data"})
PASSTHROUGH_BODY_PARAMS = frozenset({"files", "content"})
SPECIAL_PARAMS = frozenset({"path", "params", "headers", "cookies", "timeout"})
VALIDATABLE_PARAMS = frozenset({"params", "path", "headers", "cookies"})


def validate_parameter(
    param_name: str,
    param_data: Any,
    validation_model: type | None,
    method_str: str,
    path: str,
) -> Any:
    """Validate parameter using Pydantic model if provided."""
    if param_data is None:
        return None

    if isinstance(param_data, BaseModel):
        return param_data.model_dump(exclude_none=True)

    if validation_model is not None and isinstance(param_data, dict):
        try:
            validated_model = validation_model(**param_data)
            return validated_model.model_dump(exclude_none=True)
        except PydanticValidationError as e:
            dummy_response = httpx.Response(
                status_code=httpx.codes.BAD_REQUEST,
                request=httpx.Request(method_str, path),
            )
            raise ValidationError(
                f"Validation failed for '{param_name}' parameter",
                dummy_response,
                e.errors(),
                raw_data=param_data,
            ) from e

    return param_data


def build_request_params(
    endpoint: BaseEndpoint,
    client_config: ClientConfig,
    kwargs: dict[str, Any],
    request_model: type | None = None,
    query_model: type | None = None,
    path_model: type | None = None,
    headers_model: type | None = None,
    cookies_model: type | None = None,
) -> dict[str, Any]:
    """Build httpx request parameters from endpoint and client config."""
    request_params: dict[str, Any] = {
        "headers": {**client_config["headers"], **endpoint.headers},
        "timeout": endpoint.timeout or client_config["timeout"],
    }

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
    """Validate and add body parameters to request."""
    for param in VALIDATED_BODY_PARAMS:
        if param not in kwargs:
            continue

        body_data = kwargs[param]

        if request_model is not None:
            try:
                validated_request: BaseModel
                if isinstance(body_data, BaseModel):
                    if isinstance(body_data, request_model):
                        validated_request = body_data  # type: ignore[assignment]
                    else:
                        validated_request = request_model(**body_data.model_dump())
                else:
                    validated_request = request_model(**body_data)

                request_params[param] = validated_request.model_dump()
            except PydanticValidationError as e:
                dummy_response = httpx.Response(
                    status_code=httpx.codes.BAD_REQUEST,
                    request=httpx.Request(method_str, path),
                )
                raise ValidationError(
                    f"Request validation failed for '{param}' parameter",
                    dummy_response,
                    e.errors(),
                    raw_data=body_data,
                ) from e
        else:
            request_params[param] = body_data

    for param in PASSTHROUGH_BODY_PARAMS:
        if param in kwargs:
            request_params[param] = kwargs[param]


def validate_and_add_params(
    request_params: dict[str, Any],
    kwargs: dict[str, Any],
    query_model: type | None,
    path_model: type | None,
    headers_model: type | None,
    cookies_model: type | None,
    endpoint: BaseEndpoint,
    method_str: str,
    path: str,
) -> None:
    """Validate and add query, headers, and cookies parameters to request."""
    params_data = kwargs.get("params")
    if params_data is not None:
        validated_params = validate_parameter(
            "params", params_data, query_model, method_str, path
        )
        if validated_params is not None:
            request_params["params"] = validated_params

    headers_data = kwargs.get("headers")
    if headers_data is not None:
        validated_headers = validate_parameter(
            "headers", headers_data, headers_model, method_str, path
        )
        if validated_headers is not None:
            request_params["headers"] = {
                **request_params.get("headers", {}),
                **validated_headers,
            }

    cookies_data = kwargs.get("cookies")
    if cookies_data is not None:
        validated_cookies = validate_parameter(
            "cookies", cookies_data, cookies_model, method_str, path
        )
        if validated_cookies is not None:
            request_params["cookies"] = validated_cookies


def convert_method_to_string(method: HTTPMethod | str) -> str:
    """Convert HTTPMethod enum to string."""
    return method.value if isinstance(method, HTTPMethod) else method
