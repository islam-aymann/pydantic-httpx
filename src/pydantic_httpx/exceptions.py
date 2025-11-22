"""Exception classes for pydantic-httpx."""

from typing import Any

import httpx
from pydantic_core import ErrorDetails


class ResponseError(Exception):
    """
    Base exception for all pydantic-httpx errors.

    Raised when an HTTP request fails or response validation fails.
    Always includes the httpx.Response object for inspection.

    Attributes:
        message: Human-readable error message.
        response: The httpx.Response object.
        status_code: HTTP status code from the response.
    """

    def __init__(self, message: str, response: httpx.Response) -> None:
        super().__init__(message)
        self.message = message
        self.response = response
        self.status_code = response.status_code

    @property
    def is_client_error(self) -> bool:
        """Check if this is a 4xx client error."""
        return self.response.is_client_error

    @property
    def is_server_error(self) -> bool:
        """Check if this is a 5xx server error."""
        return self.response.is_server_error

    @property
    def is_error(self) -> bool:
        """Check if this is an error (4xx or 5xx)."""
        return self.response.is_error

    def __str__(self) -> str:
        return f"{self.message} (status: {self.status_code})"


class HTTPError(ResponseError):
    """
    Raised when the HTTP status code indicates an error (4xx or 5xx).

    This is raised when raise_on_error=True in config and the response
    status code is >= BAD_REQUEST (400).
    """

    def __init__(self, response: httpx.Response) -> None:
        message = (
            f"HTTP error occurred: {response.status_code} {response.reason_phrase}"
        )
        super().__init__(message, response)


class ValidationError(ResponseError):
    """
    Raised when response validation against a Pydantic model fails.

    Attributes:
        validation_errors: List of Pydantic validation errors.
        raw_data: The raw data that failed validation.
    """

    def __init__(
        self,
        message: str,
        response: httpx.Response,
        validation_errors: list[ErrorDetails],
        raw_data: Any = None,
    ) -> None:
        super().__init__(message, response)
        self.validation_errors = validation_errors
        self.raw_data = raw_data

    def __str__(self) -> str:
        error_count = len(self.validation_errors)
        return f"{self.message} ({error_count} validation error(s))"


class RequestTimeoutError(Exception):
    """
    Raised when a request times out.

    Note: This wraps httpx.TimeoutException for consistency.
    Named RequestTimeoutError to avoid shadowing built-in TimeoutError.
    """

    def __init__(self, message: str, timeout: float) -> None:
        super().__init__(message)
        self.message = message
        self.timeout = timeout

    def __str__(self) -> str:
        return f"{self.message} (timeout: {self.timeout}s)"


class RequestError(Exception):
    """
    Raised when there's an error building or sending the request.

    This includes network errors, connection errors, etc.
    """

    def __init__(
        self,
        message: str,
        original_exception: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.original_exception = original_exception

    def __str__(self) -> str:
        if self.original_exception:
            return f"{self.message}: {self.original_exception}"
        return self.message
