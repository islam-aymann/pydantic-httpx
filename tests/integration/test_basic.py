"""Integration tests for client, resource, and endpoint together."""

from typing import Annotated

import pytest
from httpx import codes
from pydantic import BaseModel
from pytest_httpx import HTTPXMock

from pydantic_httpx import (
    DELETE,
    GET,
    POST,
    BaseResource,
    Client,
    ClientConfig,
    DataResponse,
    HTTPError,
    ResourceConfig,
    ResponseEndpoint,
    ValidationError,
)


class User(BaseModel):
    """Test model for User."""

    id: int
    name: str
    email: str


class CreateUserRequest(BaseModel):
    """Request model for creating a user."""

    name: str
    email: str


class UserResource(BaseResource):
    """Resource for user endpoints."""

    resource_config = ResourceConfig(prefix="/users")

    get: Annotated[ResponseEndpoint[User], GET("/{id}")]
    list_all: Annotated[ResponseEndpoint[list[User]], GET("")]
    create: Annotated[ResponseEndpoint[User, CreateUserRequest], POST("")]
    delete: Annotated[ResponseEndpoint[None], DELETE("/{id}")]


class APIClient(Client):
    """Test client with user resource."""

    client_config = ClientConfig(base_url="https://api.example.com")

    users: UserResource


class TestIntegration:
    """Integration tests for the complete system."""

    def test_client_initialization(self) -> None:
        """Test that client initializes with resources."""
        client = APIClient()

        assert hasattr(client, "users")
        assert isinstance(client.users, UserResource)
        assert client.users._client is client

    def test_get_single_user(self, httpx_mock: HTTPXMock) -> None:
        """Test GET request for single user."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="GET",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )

        client = APIClient()
        response = client.users.get(id=1)

        assert isinstance(response, DataResponse)
        assert isinstance(response.data, User)
        assert response.data.id == 1
        assert response.data.name == "John"
        assert response.data.email == "john@example.com"
        assert response.status_code == codes.OK

    def test_list_users(self, httpx_mock: HTTPXMock) -> None:
        """Test GET request for list of users."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="GET",
            json=[
                {"id": 1, "name": "John", "email": "john@example.com"},
                {"id": 2, "name": "Jane", "email": "jane@example.com"},
            ],
        )

        client = APIClient()
        response = client.users.list_all()

        assert isinstance(response, DataResponse)
        assert isinstance(response.data, list)
        assert len(response.data) == 2
        assert all(isinstance(user, User) for user in response.data)
        assert response.data[0].name == "John"
        assert response.data[1].name == "Jane"

    def test_create_user(self, httpx_mock: HTTPXMock) -> None:
        """Test POST request to create user."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="POST",
            json={"id": 3, "name": "Alice", "email": "alice@example.com"},
            status_code=codes.CREATED,
        )

        client = APIClient()
        response = client.users.create(
            json={"name": "Alice", "email": "alice@example.com"}
        )

        assert isinstance(response, DataResponse)
        assert isinstance(response.data, User)
        assert response.data.id == 3
        assert response.data.name == "Alice"
        assert response.status_code == codes.CREATED

    def test_delete_user(self, httpx_mock: HTTPXMock) -> None:
        """Test DELETE request."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="DELETE",
            status_code=codes.NO_CONTENT,
        )

        client = APIClient()
        response = client.users.delete(id=1)

        assert isinstance(response, DataResponse)
        assert response.data is None
        assert response.status_code == codes.NO_CONTENT

    def test_path_parameter_formatting(self, httpx_mock: HTTPXMock) -> None:
        """Test that path parameters are correctly formatted."""
        httpx_mock.add_response(
            url="https://api.example.com/users/42",
            method="GET",
            json={"id": 42, "name": "Test", "email": "test@example.com"},
        )

        client = APIClient()
        response = client.users.get(id=42)

        assert response.data.id == 42

    def test_validation_error(self, httpx_mock: HTTPXMock) -> None:
        """Test that validation errors are raised for invalid responses."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="GET",
            json={"invalid": "data"},  # Missing required fields
        )

        client = APIClient()

        with pytest.raises(ValidationError) as exc_info:
            client.users.get(id=1)

        assert "Response validation failed" in str(exc_info.value)
        assert exc_info.value.validation_errors

    def test_http_error(self, httpx_mock: HTTPXMock) -> None:
        """Test that HTTP errors are raised for error status codes."""

        class ErrorClient(Client):
            client_config = ClientConfig(
                base_url="https://api.example.com", raise_on_error=True
            )
            users: UserResource

        httpx_mock.add_response(
            url="https://api.example.com/users/999",
            method="GET",
            status_code=codes.NOT_FOUND,
            text="Not Found",
        )

        client = ErrorClient()

        with pytest.raises(HTTPError) as exc_info:
            client.users.get(id=999)

        assert exc_info.value.status_code == codes.NOT_FOUND
        assert exc_info.value.is_client_error

    def test_context_manager(self, httpx_mock: HTTPXMock) -> None:
        """Test client works as context manager."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="GET",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )

        with APIClient() as client:
            response = client.users.get(id=1)
            assert response.data.name == "John"

    def test_data_dump_method(self, httpx_mock: HTTPXMock) -> None:
        """Test data_dump() method returns dict."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="GET",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )

        client = APIClient()
        response = client.users.get(id=1)

        data_dict = response.data_dump()
        assert isinstance(data_dict, dict)
        assert data_dict == {"id": 1, "name": "John", "email": "john@example.com"}

    def test_resource_without_client_raises_error(self) -> None:
        """Test that calling endpoint without client raises RuntimeError."""
        resource = UserResource()

        with pytest.raises(RuntimeError, match="not bound to a client"):
            resource.get(id=1)

    def test_endpoint_returns_data_only(self, httpx_mock: HTTPXMock) -> None:
        """Test that ResponseEndpoint[T] returns DataResponse[T]."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            json={"id": 1, "name": "Alice", "email": "alice@example.com"},
            status_code=200,
        )

        class SimpleClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            get_user: Annotated[ResponseEndpoint[User], GET("/users/{id}")]

        client = SimpleClient()
        response = client.get_user(id=1)

        # Verify result is DataResponse[User]
        assert isinstance(response, DataResponse)
        assert isinstance(response.data, User)
        assert response.data.id == 1
        assert response.data.name == "Alice"

    def test_endpoint_with_list_returns_data_only(self, httpx_mock: HTTPXMock) -> None:
        """Test that ResponseEndpoint[list[T]] returns DataResponse[list[T]]."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            json=[
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
            ],
            status_code=200,
        )

        class SimpleClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            list_users: Annotated[ResponseEndpoint[list[User]], GET("/users")]

        client = SimpleClient()
        response = client.list_users()

        # Verify result is DataResponse[list[User]]
        assert isinstance(response, DataResponse)
        assert isinstance(response.data, list)
        assert len(response.data) == 2
        assert all(isinstance(u, User) for u in response.data)
        assert response.data[0].name == "Alice"
        assert response.data[1].name == "Bob"

    def test_response_endpoint_returns_full_response(
        self,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Test that ResponseEndpoint[T] returns DataResponse[T]."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            json={"id": 1, "name": "Alice", "email": "alice@example.com"},
            status_code=200,
            headers={"X-Custom": "value"},
        )

        class FullResponseClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            get_user: Annotated[ResponseEndpoint[User], GET("/users/{id}")]

        client = FullResponseClient()
        result = client.get_user(id=1)

        # Verify result is DataResponse[User]
        assert isinstance(result, DataResponse)
        assert result.status_code == 200
        assert result.headers["X-Custom"] == "value"
        assert isinstance(result.data, User)
        assert result.data.name == "Alice"

    def test_mixed_endpoint_types(self, httpx_mock: HTTPXMock) -> None:
        """Test using ResponseEndpoint[T] for different response types."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            json=[{"id": 1, "name": "Alice", "email": "alice@example.com"}],
            status_code=200,
        )
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            json={"id": 1, "name": "Alice", "email": "alice@example.com"},
            status_code=200,
        )

        class MixedClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            list_users: Annotated[ResponseEndpoint[list[User]], GET("/users")]
            get_user: Annotated[ResponseEndpoint[User], GET("/users/{id}")]

        client = MixedClient()

        # Both return DataResponse
        list_response = client.list_users()
        assert isinstance(list_response, DataResponse)
        assert isinstance(list_response.data, list)
        assert isinstance(list_response.data[0], User)

        # ResponseEndpoint[T] returns DataResponse
        response = client.get_user(id=1)
        assert isinstance(response, DataResponse)
        assert isinstance(response.data, User)
