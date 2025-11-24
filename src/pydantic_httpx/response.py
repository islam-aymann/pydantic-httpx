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
        >>> response = client.users.get(path={"id": 1})
        >>> user = response.data
        >>> status = response.status_code
        >>> headers = response.headers
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
        """Get the validated and parsed response data (Pydantic model)."""
        return self._data

    def data_dump(self) -> dict[str, Any] | list[dict[str, Any]] | None:
        """
        Get the validated data as a dictionary.

        Uses Pydantic's model_dump() to serialize the model to a dict.
        Returns None if data is None (e.g., DELETE responses).
        """
        if self._data is None:
            return None
        if hasattr(self._data, "model_dump"):
            result: dict[str, Any] = self._data.model_dump()
            return result
        if isinstance(self._data, list):
            return [
                item.model_dump() if hasattr(item, "model_dump") else item
                for item in self._data
            ]
        if isinstance(self._data, dict):
            return self._data
        return None

    @property
    def text(self) -> str:
        """Get the raw response text (delegates to httpx.Response)."""
        return self._response.text

    @property
    def content(self) -> bytes:
        """Get the raw response content as bytes (delegates to httpx.Response)."""
        return self._response.content

    def json(self) -> Any:
        """Parse response as JSON (delegates to httpx.Response)."""
        return self._response.json()

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
        return f"{self.__class__.__name__}({self.status_code=}, {self.data=})"

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} [{self.status_code}]>"

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
