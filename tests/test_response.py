"""Tests for DataResponse wrapper."""

import httpx
import pytest
from httpx import codes
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
            codes.OK, json={"id": 1, "name": "John", "email": "john@example.com"}
        )
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        assert data_response.data == user
        assert data_response.response is response
        assert data_response.status_code == codes.OK

    def test_data_property(self) -> None:
        """Test accessing data property."""
        response = httpx.Response(codes.OK)
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        assert isinstance(data_response.data, User)
        assert data_response.data.id == 1
        assert data_response.data.name == "John"

    def test_response_property(self) -> None:
        """Test accessing raw response."""
        response = httpx.Response(codes.OK, headers={"X-Custom": "value"})
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        assert data_response.response is response
        assert data_response.response.headers["X-Custom"] == "value"

    def test_status_code_property(self) -> None:
        """Test status_code convenience property."""
        response = httpx.Response(codes.CREATED)
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        assert data_response.status_code == codes.CREATED

    def test_headers_property(self) -> None:
        """Test headers convenience property."""
        response = httpx.Response(
            codes.OK, headers={"Content-Type": "application/json"}
        )
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        assert "Content-Type" in data_response.headers
        assert data_response.headers["Content-Type"] == "application/json"

    def test_url_property(self) -> None:
        """Test url convenience property."""
        response = httpx.Response(
            codes.OK, request=httpx.Request("GET", "https://api.example.com/users/1")
        )
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        assert str(data_response.url) == "https://api.example.com/users/1"

    def test_is_success_property(self) -> None:
        """Test is_success property for 2xx status codes."""
        response_200 = httpx.Response(codes.OK)
        response_201 = httpx.Response(codes.CREATED)
        response_400 = httpx.Response(codes.BAD_REQUEST)

        user = User(id=1, name="John", email="john@example.com")

        assert DataResponse(response_200, user).is_success is True
        assert DataResponse(response_201, user).is_success is True
        assert DataResponse(response_400, user).is_success is False

    def test_is_error_property(self) -> None:
        """Test is_error property for 4xx/5xx status codes."""
        response_200 = httpx.Response(codes.OK)
        response_400 = httpx.Response(codes.BAD_REQUEST)
        response_500 = httpx.Response(codes.INTERNAL_SERVER_ERROR)

        user = User(id=1, name="John", email="john@example.com")

        assert DataResponse(response_200, user).is_error is False
        assert DataResponse(response_400, user).is_error is True
        assert DataResponse(response_500, user).is_error is True

    def test_is_client_error_property(self) -> None:
        """Test is_client_error property for 4xx status codes."""
        response_404 = httpx.Response(codes.NOT_FOUND)
        response_500 = httpx.Response(codes.INTERNAL_SERVER_ERROR)

        user = User(id=1, name="John", email="john@example.com")

        assert DataResponse(response_404, user).is_client_error is True
        assert DataResponse(response_500, user).is_client_error is False

    def test_is_server_error_property(self) -> None:
        """Test is_server_error property for 5xx status codes."""
        response_404 = httpx.Response(codes.NOT_FOUND)
        response_500 = httpx.Response(codes.INTERNAL_SERVER_ERROR)

        user = User(id=1, name="John", email="john@example.com")

        assert DataResponse(response_404, user).is_server_error is False
        assert DataResponse(response_500, user).is_server_error is True

    def test_repr(self) -> None:
        """Test __repr__ method."""
        response = httpx.Response(codes.OK)
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        repr_str = repr(data_response)
        assert "DataResponse" in repr_str
        assert "200" in repr_str

    def test_str(self) -> None:
        """Test __str__ method."""
        response = httpx.Response(codes.CREATED)
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        str_repr = str(data_response)
        assert "DataResponse" in str_repr
        assert "201" in str_repr

    def test_direct_attribute_access(self) -> None:
        """Test direct attribute access to data (convenience)."""
        response = httpx.Response(codes.OK)
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        # Should be able to access data.name directly
        assert data_response.name == "John"  # type: ignore
        assert data_response.email == "john@example.com"  # type: ignore
        assert data_response.id == 1  # type: ignore

    def test_attribute_error_on_missing_attribute(self) -> None:
        """Test that accessing non-existent attributes raises AttributeError."""
        response = httpx.Response(codes.OK)
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        with pytest.raises(AttributeError, match="has no attribute 'nonexistent'"):
            _ = data_response.nonexistent  # type: ignore

    def test_with_list_data(self) -> None:
        """Test DataResponse with list of models."""
        response = httpx.Response(codes.OK)
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
        response = httpx.Response(codes.OK)
        data = {"status": "ok", "count": 42}
        data_response = DataResponse(response, data)

        assert isinstance(data_response.data, dict)
        assert data_response.data["status"] == "ok"
        assert data_response.data["count"] == 42

    def test_with_none_data(self) -> None:
        """Test DataResponse with None data (e.g., DELETE responses)."""
        response = httpx.Response(codes.NO_CONTENT)
        data_response = DataResponse(response, None)

        assert data_response.data is None
        assert data_response.status_code == codes.NO_CONTENT

    def test_data_dump_with_pydantic_model(self) -> None:
        """Test data_dump method with Pydantic model."""
        response = httpx.Response(codes.OK)
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        data_dump = data_response.data_dump()
        assert isinstance(data_dump, dict)
        assert data_dump == {"id": 1, "name": "John", "email": "john@example.com"}

    def test_data_dump_with_list_of_models(self) -> None:
        """Test data_dump method with list of Pydantic models."""
        response = httpx.Response(codes.OK)
        users = [
            User(id=1, name="John", email="john@example.com"),
            User(id=2, name="Jane", email="jane@example.com"),
        ]
        data_response = DataResponse(response, users)

        data_dump = data_response.data_dump()
        assert isinstance(data_dump, list)
        assert len(data_dump) == 2
        assert data_dump == [
            {"id": 1, "name": "John", "email": "john@example.com"},
            {"id": 2, "name": "Jane", "email": "jane@example.com"},
        ]

    def test_data_dump_with_none(self) -> None:
        """Test data_dump method with None data (e.g., DELETE responses)."""
        response = httpx.Response(codes.NO_CONTENT)
        data_response = DataResponse(response, None)

        assert data_response.data_dump() is None

    def test_data_dump_with_dict(self) -> None:
        """Test data_dump method with dict data (non-Pydantic)."""
        response = httpx.Response(codes.OK)
        data = {"status": "ok", "count": 42}
        data_response = DataResponse(response, data)

        data_dump = data_response.data_dump()
        assert data_dump == {"status": "ok", "count": 42}

    def test_text_property(self) -> None:
        """Test text property delegates to httpx.Response."""
        response = httpx.Response(codes.OK, text="Hello, World!")
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        assert data_response.text == "Hello, World!"
        assert data_response.text == response.text

    def test_content_property(self) -> None:
        """Test content property delegates to httpx.Response."""
        response = httpx.Response(codes.OK, content=b"Binary content")
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        assert data_response.content == b"Binary content"
        assert data_response.content == response.content

    def test_json_method(self) -> None:
        """Test json() method delegates to httpx.Response."""
        json_data = {"id": 1, "name": "John", "email": "john@example.com"}
        response = httpx.Response(codes.OK, json=json_data)
        user = User(id=1, name="John", email="john@example.com")
        data_response = DataResponse(response, user)

        assert data_response.json() == json_data
        assert data_response.json() == response.json()
