"""Tests for exception classes."""

import httpx

from pydantic_httpx import HTTPError, RequestError, ResponseError, ValidationError


class TestResponseError:
    """Tests for ResponseError base class."""

    def test_basic_error(self) -> None:
        """Test basic ResponseError creation."""
        response = httpx.Response(404, text="Not Found")
        error = ResponseError("Resource not found", response)

        assert error.message == "Resource not found"
        assert error.response is response
        assert error.status_code == 404
        assert str(error) == "Resource not found (status: 404)"

    def test_is_client_error(self) -> None:
        """Test is_client_error property for 4xx status codes."""
        response_400 = httpx.Response(400)
        response_404 = httpx.Response(404)
        response_499 = httpx.Response(499)
        response_500 = httpx.Response(500)

        assert ResponseError("", response_400).is_client_error is True
        assert ResponseError("", response_404).is_client_error is True
        assert ResponseError("", response_499).is_client_error is True
        assert ResponseError("", response_500).is_client_error is False

    def test_is_server_error(self) -> None:
        """Test is_server_error property for 5xx status codes."""
        response_500 = httpx.Response(500)
        response_502 = httpx.Response(502)
        response_599 = httpx.Response(599)
        response_404 = httpx.Response(404)

        assert ResponseError("", response_500).is_server_error is True
        assert ResponseError("", response_502).is_server_error is True
        assert ResponseError("", response_599).is_server_error is True
        assert ResponseError("", response_404).is_server_error is False


class TestHTTPError:
    """Tests for HTTPError."""

    def test_http_error_message(self) -> None:
        """Test HTTPError creates appropriate message."""
        response = httpx.Response(404, text="Not Found")
        error = HTTPError(response)

        assert "HTTP error occurred" in error.message
        assert "404" in error.message
        assert error.status_code == 404
        assert error.response is response

    def test_http_error_inherits_from_response_error(self) -> None:
        """Test that HTTPError is a ResponseError."""
        response = httpx.Response(500)
        error = HTTPError(response)

        assert isinstance(error, ResponseError)
        assert error.is_server_error is True


class TestValidationError:
    """Tests for ValidationError."""

    def test_validation_error_with_errors(self) -> None:
        """Test ValidationError with validation errors."""
        response = httpx.Response(200, json={"invalid": "data"})
        validation_errors = [
            {"loc": ["name"], "msg": "field required", "type": "value_error.missing"},
            {"loc": ["email"], "msg": "field required", "type": "value_error.missing"},
        ]

        error = ValidationError(
            "Response validation failed",
            response,
            validation_errors,
            raw_data={"invalid": "data"},
        )

        assert error.message == "Response validation failed"
        assert error.validation_errors == validation_errors
        assert error.raw_data == {"invalid": "data"}
        assert len(error.validation_errors) == 2
        assert "2 validation error(s)" in str(error)

    def test_validation_error_inherits_from_response_error(self) -> None:
        """Test that ValidationError is a ResponseError."""
        response = httpx.Response(200)
        error = ValidationError("Validation failed", response, [])

        assert isinstance(error, ResponseError)


class TestRequestError:
    """Tests for RequestError."""

    def test_basic_request_error(self) -> None:
        """Test basic RequestError creation."""
        error = RequestError("Connection failed")

        assert error.message == "Connection failed"
        assert error.original_exception is None
        assert str(error) == "Connection failed"

    def test_request_error_with_original_exception(self) -> None:
        """Test RequestError wrapping another exception."""
        original = ValueError("Invalid URL")
        error = RequestError("Request failed", original_exception=original)

        assert error.message == "Request failed"
        assert error.original_exception is original
        assert "Invalid URL" in str(error)
