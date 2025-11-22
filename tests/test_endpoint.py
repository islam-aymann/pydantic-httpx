"""Tests for Endpoint metadata class."""

import pytest
from pydantic import BaseModel

from pydantic_httpx.endpoint import (
    DELETE,
    GET,
    HEAD,
    OPTIONS,
    PATCH,
    POST,
    PUT,
    BaseEndpoint,
    Endpoint,
)
from pydantic_httpx.types import HTTPMethod


class User(BaseModel):
    """Test model for User."""

    id: int
    name: str


class TestEndpoint:
    """Tests for Endpoint metadata."""

    def test_basic_endpoint_creation(self) -> None:
        """Test creating a basic endpoint."""
        endpoint = Endpoint("GET", "/users")

        assert endpoint.method == "GET"
        assert endpoint.path == "/users"
        assert endpoint.query_model is None
        assert endpoint.timeout is None
        assert endpoint.headers == {}

    def test_endpoint_with_path_parameter(self) -> None:
        """Test endpoint with path parameters."""
        endpoint = Endpoint("GET", "/users/{id}")

        assert endpoint.path == "/users/{id}"
        assert endpoint.get_path_params() == ["id"]

    def test_endpoint_with_multiple_path_parameters(self) -> None:
        """Test endpoint with multiple path parameters."""
        endpoint = Endpoint("GET", "/users/{user_id}/posts/{post_id}")

        params = endpoint.get_path_params()
        assert params == ["user_id", "post_id"]

    def test_endpoint_auto_adds_leading_slash(self) -> None:
        """Test that endpoint automatically adds leading slash if missing."""
        endpoint = Endpoint("GET", "users")

        assert endpoint.path == "/users"

    def test_endpoint_with_empty_path(self) -> None:
        """Test endpoint with empty path (root)."""
        endpoint = Endpoint("GET", "")

        assert endpoint.path == "/"

    def test_endpoint_with_query_model(self) -> None:
        """Test endpoint with query parameters model."""
        endpoint = Endpoint("GET", "/users", query_model=User)

        assert endpoint.query_model is User

    def test_endpoint_with_timeout(self) -> None:
        """Test endpoint with custom timeout."""
        endpoint = Endpoint("GET", "/users", timeout=10.0)

        assert endpoint.timeout == 10.0

    def test_endpoint_with_headers(self) -> None:
        """Test endpoint with custom headers."""
        headers = {"X-Custom": "value"}
        endpoint = Endpoint("GET", "/users", headers=headers)

        assert endpoint.headers == headers

    def test_invalid_http_method(self) -> None:
        """Test that invalid HTTP method raises ValueError."""
        with pytest.raises(ValueError, match="Invalid HTTP method"):
            Endpoint("INVALID", "/users")

    def test_get_path_params_no_params(self) -> None:
        """Test get_path_params with no parameters."""
        endpoint = Endpoint("GET", "/users")

        assert endpoint.get_path_params() == []

    def test_format_path_with_single_param(self) -> None:
        """Test formatting path with single parameter."""
        endpoint = Endpoint("GET", "/users/{id}")

        formatted = endpoint.format_path(id=123)
        assert formatted == "/users/123"

    def test_format_path_with_multiple_params(self) -> None:
        """Test formatting path with multiple parameters."""
        endpoint = Endpoint("GET", "/users/{user_id}/posts/{post_id}")

        formatted = endpoint.format_path(user_id=1, post_id=42)
        assert formatted == "/users/1/posts/42"

    def test_format_path_missing_required_param(self) -> None:
        """Test that formatting path without required params raises ValueError."""
        endpoint = Endpoint("GET", "/users/{id}")

        with pytest.raises(ValueError, match="Missing required path parameters"):
            endpoint.format_path()

    def test_format_path_with_extra_params(self) -> None:
        """Test formatting path with extra parameters (should be ignored)."""
        endpoint = Endpoint("GET", "/users/{id}")

        formatted = endpoint.format_path(id=123, extra="ignored")
        assert formatted == "/users/123"

    def test_format_path_converts_to_string(self) -> None:
        """Test that format_path converts non-string values to strings."""
        endpoint = Endpoint("GET", "/users/{id}")

        formatted = endpoint.format_path(id=123)
        assert formatted == "/users/123"
        assert isinstance(formatted, str)

    def test_repr(self) -> None:
        """Test __repr__ method."""
        endpoint = Endpoint("GET", "/users/{id}")

        repr_str = repr(endpoint)
        assert "Endpoint" in repr_str
        assert "GET" in repr_str
        assert "/users/{id}" in repr_str

    def test_all_http_methods(self) -> None:
        """Test all valid HTTP methods."""
        methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]

        for method in methods:
            endpoint = Endpoint(method, "/test")
            assert endpoint.method == method


class TestMethodSpecificEndpoints:
    """Tests for method-specific endpoint classes (GET, POST, etc.)."""

    def test_get_endpoint(self) -> None:
        """Test GET endpoint class."""
        endpoint = GET("/users/{id}")

        assert endpoint.method == HTTPMethod.GET
        assert endpoint.path == "/users/{id}"
        assert endpoint.query_model is None

    def test_post_endpoint(self) -> None:
        """Test POST endpoint class."""
        endpoint = POST("/users")

        assert endpoint.method == HTTPMethod.POST
        assert endpoint.path == "/users"

    def test_put_endpoint(self) -> None:
        """Test PUT endpoint class."""
        endpoint = PUT("/users/{id}")

        assert endpoint.method == HTTPMethod.PUT
        assert endpoint.path == "/users/{id}"

    def test_patch_endpoint(self) -> None:
        """Test PATCH endpoint class."""
        endpoint = PATCH("/users/{id}")

        assert endpoint.method == HTTPMethod.PATCH
        assert endpoint.path == "/users/{id}"

    def test_delete_endpoint(self) -> None:
        """Test DELETE endpoint class."""
        endpoint = DELETE("/users/{id}")

        assert endpoint.method == HTTPMethod.DELETE
        assert endpoint.path == "/users/{id}"

    def test_head_endpoint(self) -> None:
        """Test HEAD endpoint class."""
        endpoint = HEAD("/users/{id}")

        assert endpoint.method == HTTPMethod.HEAD
        assert endpoint.path == "/users/{id}"

    def test_options_endpoint(self) -> None:
        """Test OPTIONS endpoint class."""
        endpoint = OPTIONS("/users")

        assert endpoint.method == HTTPMethod.OPTIONS
        assert endpoint.path == "/users"

    def test_method_specific_with_all_params(self) -> None:
        """Test method-specific endpoint with all parameters."""
        headers = {"X-Custom": "value"}
        endpoint = GET(
            "/users/{id}",
            query_model=User,
            timeout=10.0,
            headers=headers,
        )

        assert endpoint.method == HTTPMethod.GET
        assert endpoint.path == "/users/{id}"
        assert endpoint.query_model is User
        assert endpoint.timeout == 10.0
        assert endpoint.headers == headers

    def test_method_specific_path_formatting(self) -> None:
        """Test that method-specific endpoints support path formatting."""
        endpoint = GET("/users/{id}/posts/{post_id}")

        params = endpoint.get_path_params()
        assert params == ["id", "post_id"]

        formatted = endpoint.format_path(id=1, post_id=42)
        assert formatted == "/users/1/posts/42"

    def test_method_specific_empty_path(self) -> None:
        """Test method-specific endpoint with empty path."""
        endpoint = GET("")

        assert endpoint.path == "/"

    def test_method_specific_no_leading_slash(self) -> None:
        """Test method-specific endpoint auto-adds leading slash."""
        endpoint = POST("users")

        assert endpoint.path == "/users"

    def test_all_method_classes_inherit_from_base(self) -> None:
        """Test that all method-specific classes inherit from BaseEndpoint."""
        endpoint_classes = [GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS]

        for endpoint_class in endpoint_classes:
            endpoint = endpoint_class("/test")
            assert isinstance(endpoint, BaseEndpoint)

    def test_generic_endpoint_validates_method(self) -> None:
        """Test that generic Endpoint class validates method."""
        # Valid methods should work
        endpoint = Endpoint("GET", "/test")
        assert endpoint.method == HTTPMethod.GET

        endpoint = Endpoint(HTTPMethod.POST, "/test")
        assert endpoint.method == HTTPMethod.POST

        # Invalid method should raise error
        with pytest.raises(ValueError, match="Invalid HTTP method"):
            Endpoint("INVALID", "/test")

    def test_method_specific_repr(self) -> None:
        """Test __repr__ for method-specific endpoints."""
        endpoint = GET("/users/{id}")

        repr_str = repr(endpoint)
        assert "GET" in repr_str
        assert "/users/{id}" in repr_str
