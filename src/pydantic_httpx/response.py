"""Response wrapper with validated data."""

from typing import Any, Generic, TypeVar

import httpx

T = TypeVar("T")


class DataResponse(Generic[T]):
    """
    Wrapper around httpx.Response with validated Pydantic data.

    This class provides access to both the validated/parsed data
    and the raw HTTP response for accessing headers, status codes, etc.

    Attributes:
        data: The validated and parsed response data (type T).
        response: The raw httpx.Response object.

    Example:
        >>> response = client.get("/users/1", response_model=User)
        >>> user = response.data  # Type: User (validated)
        >>> status = response.status_code  # 200
        >>> headers = response.headers  # httpx.Headers
    """

    def __init__(self, response: httpx.Response, data: T) -> None:
        """
        Initialize DataResponse with HTTP response and validated data.

        Args:
            response: The raw httpx.Response object.
            data: The validated data (typically a Pydantic model instance).
        """
        self._response = response
        self._data = data

    @property
    def data(self) -> T:
        """Get the validated and parsed response data."""
        return self._data

    @property
    def response(self) -> httpx.Response:
        """Get the raw httpx.Response for accessing HTTP metadata."""
        return self._response

    @property
    def status_code(self) -> int:
        """Get the HTTP status code."""
        return self._response.status_code

    @property
    def headers(self) -> httpx.Headers:
        """Get the response headers."""
        return self._response.headers

    @property
    def url(self) -> httpx.URL:
        """Get the final URL (after redirects)."""
        return self._response.url

    @property
    def is_success(self) -> bool:
        """Check if the response was successful (2xx status code)."""
        return self._response.is_success

    @property
    def is_error(self) -> bool:
        """Check if the response was an error (4xx or 5xx status code)."""
        return self._response.is_error

    @property
    def is_client_error(self) -> bool:
        """Check if the response was a client error (4xx status code)."""
        return self._response.is_client_error

    @property
    def is_server_error(self) -> bool:
        """Check if the response was a server error (5xx status code)."""
        return self._response.is_server_error

    def __repr__(self) -> str:
        cls_name = self.__class__.__name__
        status_code = self.status_code
        data = self.data
        return f"{cls_name}({status_code=}, {data=})"

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} [{self.status_code}]>"

    # Convenience: Allow direct attribute access to data
    def __getattr__(self, name: str) -> Any:
        """
        Allow direct access to data attributes.

        This enables both response.data.name and response.name patterns.
        """
        try:
            return getattr(self._data, name)
        except AttributeError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            ) from None
