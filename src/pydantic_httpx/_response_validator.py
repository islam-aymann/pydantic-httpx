"""Internal module for validating HTTP responses.

This module contains shared logic for response validation and parsing
used by both sync and async clients.
"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from typing_extensions import get_args, get_origin

from pydantic_httpx.exceptions import RequestError, ValidationError


def extract_response_model(response_type: type) -> Any:
    """
    Extract the inner type from DataResponse[T] or similar wrapper.

    Args:
        response_type: The full response type (e.g., DataResponse[User]).

    Returns:
        The inner type T, or the original type if not a generic.
    """
    args = get_args(response_type)
    return args[0] if args else response_type


def validate_response(response: httpx.Response, model: type) -> Any:
    """
    Validate response data against a Pydantic model.

    Args:
        response: The httpx response object.
        model: The Pydantic model to validate against (or list[Model], dict, None).

    Returns:
        Validated data (model instance, list of models, dict, or None).

    Raises:
        ValidationError: If response validation fails.
        RequestError: If response parsing fails.
    """
    # Handle None responses (e.g., DELETE with 204)
    if model is type(None) or response.status_code == httpx.codes.NO_CONTENT:
        return None

    # Parse JSON response
    data = None
    try:
        data = response.json()
    except Exception as e:
        raise RequestError(
            f"Failed to parse response as JSON: {e}",
            original_exception=e,
        ) from e

    # Validate based on model type
    try:
        return _validate_data_with_model(data, model)
    except PydanticValidationError as e:
        raise ValidationError(
            "Response validation failed",
            response,
            e.errors(),
            raw_data=data,
        ) from e


def _validate_data_with_model(data: Any, model: type) -> Any:
    """
    Validate data against a model type.

    Args:
        data: Parsed JSON data.
        model: Model type (BaseModel, list[BaseModel], dict, etc.).

    Returns:
        Validated data.

    Raises:
        PydanticValidationError: If validation fails.
    """
    origin = get_origin(model)

    # Handle list of models: list[User]
    if origin is list:
        item_type = get_args(model)[0] if get_args(model) else dict
        if isinstance(item_type, type) and issubclass(item_type, BaseModel):
            return [item_type(**item) for item in data]
        return data

    # Handle single Pydantic model: User
    if isinstance(model, type) and issubclass(model, BaseModel):
        return model(**data)

    # Return raw data for dict or other types
    return data
