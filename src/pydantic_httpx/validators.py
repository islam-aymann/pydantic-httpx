"""Pydantic-style validators for endpoints."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Literal

if TYPE_CHECKING:
    from pydantic_httpx.response import DataResponse

# Validator modes (like Pydantic's field validators)
ValidatorMode = Literal["before", "after", "wrap"]


@dataclass
class ValidatorInfo:
    """
    Information about an endpoint validator.

    Attributes:
        endpoint_name: Name of the endpoint this validator applies to.
        mode: Validator mode (before/after/wrap).
        func: The validator function.
    """

    endpoint_name: str
    mode: ValidatorMode
    func: Callable[..., Any]


def endpoint_validator(
    endpoint_name: str,
    *,
    mode: ValidatorMode = "after",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for endpoint validators (Pydantic-style).

    This decorator allows you to add validation, transformation, or custom
    logic to endpoints at three different stages:

    - **before**: Runs before the HTTP request (validate/transform params)
    - **after**: Runs after the HTTP request (process response)
    - **wrap**: Full control over request execution (caching, retry, etc.)

    Args:
        endpoint_name: Name of the endpoint attribute to validate.
        mode: When to run the validator ("before", "after", or "wrap").

    Returns:
        Decorator function that marks the method as a validator.

    Example (before - validate params):
        >>> class APIClient(Client):
        >>>     get_user: Endpoint[User] = GET("/users/{id}")
        >>>
        >>>     @endpoint_validator("get_user", mode="before")
        >>>     def validate_id(cls, params: dict) -> dict:
        >>>         if params["id"] <= 0:
        >>>             raise ValueError("Invalid ID")
        >>>         return params

    Example (after - process response):
        >>> class APIClient(Client):
        >>>     get_user: Endpoint[User] = GET("/users/{id}")
        >>>
        >>>     @endpoint_validator("get_user", mode="after")
        >>>     def handle_404(cls, response: DataResponse[User]) -> User | None:
        >>>         if response.status_code == 404:
        >>>             return None
        >>>         return response.data

    Example (wrap - full control):
        >>> class APIClient(Client):
        >>>     get_user: Endpoint[User] = GET("/users/{id}")
        >>>
        >>>     @endpoint_validator("get_user", mode="wrap")
        >>>     def cache(cls, handler, params: dict) -> User:
        >>>         if params["id"] in cache:
        >>>             return cache[params["id"]]
        >>>         response = handler(params)
        >>>         cache[params["id"]] = response.data
        >>>         return response.data
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Store validator metadata on the function
        if not hasattr(func, "_endpoint_validators"):
            func._endpoint_validators = []  # type: ignore[attr-defined]

        validator_info = ValidatorInfo(
            endpoint_name=endpoint_name,
            mode=mode,
            func=func,
        )
        func._endpoint_validators.append(validator_info)  # type: ignore[attr-defined]

        return func

    return decorator


def get_validators(cls: type) -> dict[str, list[ValidatorInfo]]:
    """
    Extract all endpoint validators from a class.

    Args:
        cls: The client or resource class to extract validators from.

    Returns:
        Dictionary mapping endpoint names to their list of validators.

    Example:
        >>> validators = get_validators(APIClient)
        >>> # {'get_user': [ValidatorInfo(mode='before', ...), ValidatorInfo(mode='after', ...)]}
    """
    validators: dict[str, list[ValidatorInfo]] = {}

    # Iterate through all methods in the class
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name, None)
        if attr is None:
            continue

        # Check if this method has validator metadata
        validator_list = getattr(attr, "_endpoint_validators", None)
        if validator_list:
            for validator_info in validator_list:
                endpoint_name = validator_info.endpoint_name
                if endpoint_name not in validators:
                    validators[endpoint_name] = []
                validators[endpoint_name].append(validator_info)

    return validators


def apply_before_validators(
    validators: list[ValidatorInfo],
    params: dict[str, Any],
    instance: Any,
) -> dict[str, Any]:
    """
    Apply 'before' validators to parameters.

    Args:
        validators: List of before validators.
        params: Request parameters.
        instance: Client or resource instance (for 'self' binding).

    Returns:
        Transformed parameters.
    """
    result = params
    for validator in validators:
        if validator.mode == "before":
            result = validator.func(instance.__class__, result)
    return result


def apply_after_validators(
    validators: list[ValidatorInfo],
    response: DataResponse[Any],
    instance: Any,
) -> Any:
    """
    Apply 'after' validators to response.

    Args:
        validators: List of after validators.
        response: HTTP response wrapper.
        instance: Client or resource instance (for 'self' binding).

    Returns:
        Transformed response (could be response.data, None, or custom type).
    """
    result: Any = response
    for validator in validators:
        if validator.mode == "after":
            result = validator.func(instance.__class__, result)
    return result


def apply_wrap_validator(
    validator: ValidatorInfo,
    handler: Callable[[dict[str, Any]], DataResponse[Any]],
    params: dict[str, Any],
    instance: Any,
) -> Any:
    """
    Apply a 'wrap' validator.

    Args:
        validator: The wrap validator.
        handler: The handler function to call for HTTP request.
        params: Request parameters.
        instance: Client or resource instance (for 'self' binding).

    Returns:
        Result from the wrap validator.
    """
    return validator.func(instance.__class__, handler, params)
