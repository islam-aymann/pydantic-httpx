"""Tests for DataResponse wrapper."""

import httpx
import pytest
from pydantic import BaseModel

from pydantic_httpx import DataResponse


class User(BaseModel):
    """Test model for User."""

    id: int
    name: str
    email: str


class TestDataResponse:
    """Tests for DataResponse."""

    def test_basic_data_response(self) -> None:
        """Test basic DataResponse creation."""
        response = httpx.Response(
            200, json={"id": 1, "name": "John", "email": "john@example.com"}
        )
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        assert data_response.data == user
        assert data_response.response is response
        assert data_response.status_code == 200

    def test_data_property(self) -> None:
        """Test accessing data property."""
        response = httpx.Response(200)
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        assert isinstance(data_response.data, User)
        assert data_response.data.id == 1
        assert data_response.data.name == "John"

    def test_response_property(self) -> None:
        """Test accessing raw response."""
        response = httpx.Response(200, headers={"X-Custom": "value"})
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        assert data_response.response is response
        assert data_response.response.headers["X-Custom"] == "value"

    def test_status_code_property(self) -> None:
        """Test status_code convenience property."""
        response = httpx.Response(201)
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        assert data_response.status_code == 201

    def test_headers_property(self) -> None:
        """Test headers convenience property."""
        response = httpx.Response(200, headers={"Content-Type": "application/json"})
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        assert "Content-Type" in data_response.headers
        assert data_response.headers["Content-Type"] == "application/json"

    def test_url_property(self) -> None:
        """Test url convenience property."""
        response = httpx.Response(
            200, request=httpx.Request("GET", "https://api.example.com/users/1")
        )
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        assert str(data_response.url) == "https://api.example.com/users/1"

    def test_is_success_property(self) -> None:
        """Test is_success property for 2xx status codes."""
        response_200 = httpx.Response(200)
        response_201 = httpx.Response(201)
        response_400 = httpx.Response(400)

        user = User(id=1, name="John", email="john@example.com")

        assert DataResponse(response_200, user).is_success is True
        assert DataResponse(response_201, user).is_success is True
        assert DataResponse(response_400, user).is_success is False

    def test_is_error_property(self) -> None:
        """Test is_error property for 4xx/5xx status codes."""
        response_200 = httpx.Response(200)
        response_400 = httpx.Response(400)
        response_500 = httpx.Response(500)

        user = User(id=1, name="John", email="john@example.com")

        assert DataResponse(response_200, user).is_error is False
        assert DataResponse(response_400, user).is_error is True
        assert DataResponse(response_500, user).is_error is True

    def test_is_client_error_property(self) -> None:
        """Test is_client_error property for 4xx status codes."""
        response_404 = httpx.Response(404)
        response_500 = httpx.Response(500)

        user = User(id=1, name="John", email="john@example.com")

        assert DataResponse(response_404, user).is_client_error is True
        assert DataResponse(response_500, user).is_client_error is False

    def test_is_server_error_property(self) -> None:
        """Test is_server_error property for 5xx status codes."""
        response_404 = httpx.Response(404)
        response_500 = httpx.Response(500)

        user = User(id=1, name="John", email="john@example.com")

        assert DataResponse(response_404, user).is_server_error is False
        assert DataResponse(response_500, user).is_server_error is True

    def test_repr(self) -> None:
        """Test __repr__ method."""
        response = httpx.Response(200)
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        repr_str = repr(data_response)
        assert "DataResponse" in repr_str
        assert "200" in repr_str

    def test_str(self) -> None:
        """Test __str__ method."""
        response = httpx.Response(201)
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        str_repr = str(data_response)
        assert "DataResponse" in str_repr
        assert "201" in str_repr

    def test_direct_attribute_access(self) -> None:
        """Test direct attribute access to data (convenience)."""
        response = httpx.Response(200)
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        # Should be able to access data.name directly
        assert data_response.name == "John"  # type: ignore
        assert data_response.email == "john@example.com"  # type: ignore
        assert data_response.id == 1  # type: ignore

    def test_attribute_error_on_missing_attribute(self) -> None:
        """Test that accessing non-existent attributes raises AttributeError."""
        response = httpx.Response(200)
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        with pytest.raises(AttributeError, match="has no attribute 'nonexistent'"):
            _ = data_response.nonexistent  # type: ignore

    def test_with_list_data(self) -> None:
        """Test DataResponse with list of models."""
        response = httpx.Response(200)
        users = [
            User(id=1, name="John", email="john@example.com"),
            User(id=2, name="Jane", email="jane@example.com"),
        ]
        data_response = DataResponse(response, users)

        assert isinstance(data_response.data, list)
        assert len(data_response.data) == 2
        assert all(isinstance(u, User) for u in data_response.data)

    def test_with_dict_data(self) -> None:
        """Test DataResponse with dict data."""
        response = httpx.Response(200)
        data = {"status": "ok", "count": 42}
        data_response = DataResponse(response, data)

        assert isinstance(data_response.data, dict)
        assert data_response.data["status"] == "ok"
        assert data_response.data["count"] == 42

    def test_with_none_data(self) -> None:
        """Test DataResponse with None data (e.g., DELETE responses)."""
        response = httpx.Response(204)
        data_response = DataResponse(response, None)

        assert data_response.data is None
        assert data_response.status_code == 204
