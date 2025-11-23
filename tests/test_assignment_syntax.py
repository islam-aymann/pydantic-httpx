"""
Tests for assignment syntax (Endpoint[T] = GET(...)) alongside Annotated syntax.

This test file ensures both syntaxes work identically and provide the same
type inference and runtime behavior.
"""

from typing import Annotated

import pytest
from pydantic import BaseModel
from pytest_httpx import HTTPXMock

from pydantic_httpx import (
    DELETE,
    GET,
    POST,
    AsyncClient,
    BaseResource,
    Client,
    ClientConfig,
    ResourceConfig,
)
from pydantic_httpx.types import Endpoint


class User(BaseModel):
    """User model for testing."""

    id: int
    name: str
    email: str


class CreateUserRequest(BaseModel):
    """Request model for creating users."""

    name: str
    email: str


class UpdateUserRequest(BaseModel):
    """Request model for updating users."""

    name: str | None = None
    email: str | None = None


# Test 1: Resource with assignment syntax
class UserResourceAssignment(BaseResource):
    """Resource using assignment syntax."""

    resource_config = ResourceConfig(prefix="/users")

    # Assignment syntax
    get: Endpoint[User] = GET("/{id}")
    list_all: Endpoint[list[User]] = GET("")
    create: Endpoint[User, CreateUserRequest] = POST("")
    delete: Endpoint[None] = DELETE("/{id}")


# Test 2: Resource with Annotated syntax (for comparison)
class UserResourceAnnotated(BaseResource):
    """Resource using Annotated syntax."""

    resource_config = ResourceConfig(prefix="/users")

    # Annotated syntax
    get: Annotated[Endpoint[User], GET("/{id}")]
    list_all: Annotated[Endpoint[list[User]], GET("")]
    create: Annotated[Endpoint[User, CreateUserRequest], POST("")]
    delete: Annotated[Endpoint[None], DELETE("/{id}")]


# Test 3: Client with direct endpoints using assignment syntax
class APIClientAssignment(Client):
    """Client with direct endpoints using assignment syntax."""

    client_config = ClientConfig(base_url="https://api.example.com")

    # Direct endpoints on client
    get_user: Endpoint[User] = GET("/users/{id}")
    list_users: Endpoint[list[User]] = GET("/users")


# Test 4: Client with direct endpoints using Annotated syntax
class APIClientAnnotated(Client):
    """Client with direct endpoints using Annotated syntax."""

    client_config = ClientConfig(base_url="https://api.example.com")

    # Direct endpoints on client
    get_user: Annotated[Endpoint[User], GET("/users/{id}")]
    list_users: Annotated[Endpoint[list[User]], GET("/users")]


# Test 5: Async client with assignment syntax
class AsyncAPIClientAssignment(AsyncClient):
    """Async client with assignment syntax."""

    client_config = ClientConfig(base_url="https://api.example.com")

    get_user: Endpoint[User] = GET("/users/{id}")


# Test 6: Async client with Annotated syntax
class AsyncAPIClientAnnotated(AsyncClient):
    """Async client with Annotated syntax."""

    client_config = ClientConfig(base_url="https://api.example.com")

    get_user: Annotated[Endpoint[User], GET("/users/{id}")]


class TestAssignmentSyntaxResource:
    """Test assignment syntax with BaseResource."""

    def test_get_endpoint_assignment_syntax(self, httpx_mock: HTTPXMock) -> None:
        """Test GET endpoint with assignment syntax."""

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: UserResourceAssignment

        httpx_mock.add_response(
            method="GET",
            url="https://api.example.com/users/1",
            json={"id": 1, "name": "John Doe", "email": "john@example.com"},
        )

        client = APIClient()
        response = client.users.get(id=1)

        assert response.status_code == 200
        assert response.data.id == 1
        assert response.data.name == "John Doe"
        assert response.data.email == "john@example.com"

    def test_list_endpoint_assignment_syntax(self, httpx_mock: HTTPXMock) -> None:
        """Test list endpoint with assignment syntax."""

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: UserResourceAssignment

        httpx_mock.add_response(
            method="GET",
            url="https://api.example.com/users",
            json=[
                {"id": 1, "name": "John", "email": "john@example.com"},
                {"id": 2, "name": "Jane", "email": "jane@example.com"},
            ],
        )

        client = APIClient()
        response = client.users.list_all()

        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0].name == "John"
        assert response.data[1].name == "Jane"

    def test_delete_endpoint_assignment_syntax(self, httpx_mock: HTTPXMock) -> None:
        """Test DELETE endpoint with assignment syntax."""

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: UserResourceAssignment

        httpx_mock.add_response(
            method="DELETE",
            url="https://api.example.com/users/1",
            status_code=204,
        )

        client = APIClient()
        response = client.users.delete(id=1)

        assert response.status_code == 204


class TestAssignmentSyntaxVsAnnotated:
    """Test that assignment syntax behaves identically to Annotated syntax."""

    def test_both_syntaxes_produce_same_result(self, httpx_mock: HTTPXMock) -> None:
        """Verify both syntaxes produce identical results."""

        class ClientAssignment(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: UserResourceAssignment

        class ClientAnnotated(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: UserResourceAnnotated

        user_data = {"id": 1, "name": "John", "email": "john@example.com"}

        # Mock for assignment syntax
        httpx_mock.add_response(
            method="GET",
            url="https://api.example.com/users/1",
            json=user_data,
        )

        # Mock for Annotated syntax
        httpx_mock.add_response(
            method="GET",
            url="https://api.example.com/users/1",
            json=user_data,
        )

        client_assignment = ClientAssignment()
        client_annotated = ClientAnnotated()

        response_assignment = client_assignment.users.get(id=1)
        response_annotated = client_annotated.users.get(id=1)

        # Both should have identical responses
        assert response_assignment.status_code == response_annotated.status_code
        assert response_assignment.data.id == response_annotated.data.id
        assert response_assignment.data.name == response_annotated.data.name
        assert response_assignment.data.email == response_annotated.data.email


class TestAssignmentSyntaxDirectEndpoints:
    """Test assignment syntax with direct endpoints on Client."""

    def test_direct_endpoint_on_client_assignment(self, httpx_mock: HTTPXMock) -> None:
        """Test direct endpoint on client with assignment syntax."""
        httpx_mock.add_response(
            method="GET",
            url="https://api.example.com/users/1",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )

        client = APIClientAssignment()
        response = client.get_user(id=1)

        assert response.status_code == 200
        assert response.data.id == 1
        assert response.data.name == "John"

    def test_direct_endpoint_on_client_annotated(self, httpx_mock: HTTPXMock) -> None:
        """Test direct endpoint on client with Annotated syntax."""
        httpx_mock.add_response(
            method="GET",
            url="https://api.example.com/users/1",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )

        client = APIClientAnnotated()
        response = client.get_user(id=1)

        assert response.status_code == 200
        assert response.data.id == 1
        assert response.data.name == "John"

    def test_both_direct_syntax_produce_same_result(
        self, httpx_mock: HTTPXMock
    ) -> None:
        """Verify direct endpoints work identically with both syntaxes."""
        user_data = {"id": 1, "name": "John", "email": "john@example.com"}

        httpx_mock.add_response(
            method="GET",
            url="https://api.example.com/users/1",
            json=user_data,
        )
        httpx_mock.add_response(
            method="GET",
            url="https://api.example.com/users/1",
            json=user_data,
        )

        client_assignment = APIClientAssignment()
        client_annotated = APIClientAnnotated()

        response_assignment = client_assignment.get_user(id=1)
        response_annotated = client_annotated.get_user(id=1)

        assert response_assignment.status_code == response_annotated.status_code
        assert response_assignment.data.id == response_annotated.data.id


class TestAssignmentSyntaxAsync:
    """Test assignment syntax with AsyncClient."""

    @pytest.mark.asyncio
    async def test_async_client_assignment_syntax(self, httpx_mock: HTTPXMock) -> None:
        """Test async client with assignment syntax."""
        httpx_mock.add_response(
            method="GET",
            url="https://api.example.com/users/1",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )

        async with AsyncAPIClientAssignment() as client:
            response = await client.get_user(id=1)

        assert response.status_code == 200
        assert response.data.id == 1
        assert response.data.name == "John"

    @pytest.mark.asyncio
    async def test_async_client_annotated_syntax(self, httpx_mock: HTTPXMock) -> None:
        """Test async client with Annotated syntax."""
        httpx_mock.add_response(
            method="GET",
            url="https://api.example.com/users/1",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )

        async with AsyncAPIClientAnnotated() as client:
            response = await client.get_user(id=1)

        assert response.status_code == 200
        assert response.data.id == 1
        assert response.data.name == "John"

    @pytest.mark.asyncio
    async def test_async_both_syntaxes_identical(self, httpx_mock: HTTPXMock) -> None:
        """Verify both syntaxes produce identical results in async context."""
        user_data = {"id": 1, "name": "John", "email": "john@example.com"}

        httpx_mock.add_response(
            method="GET",
            url="https://api.example.com/users/1",
            json=user_data,
        )
        httpx_mock.add_response(
            method="GET",
            url="https://api.example.com/users/1",
            json=user_data,
        )

        async with AsyncAPIClientAssignment() as client_assignment:
            response_assignment = await client_assignment.get_user(id=1)

        async with AsyncAPIClientAnnotated() as client_annotated:
            response_annotated = await client_annotated.get_user(id=1)

        assert response_assignment.status_code == response_annotated.status_code
        assert response_assignment.data.id == response_annotated.data.id


class TestAssignmentSyntaxMixed:
    """Test mixing both syntaxes in the same resource/client."""

    def test_mixed_syntax_in_resource(self, httpx_mock: HTTPXMock) -> None:
        """Test that both syntaxes can coexist in same resource."""

        class MixedResource(BaseResource):
            resource_config = ResourceConfig(prefix="/users")

            # Assignment syntax
            get: Endpoint[User] = GET("/{id}")

            # Annotated syntax
            list_all: Annotated[Endpoint[list[User]], GET("")]

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: MixedResource

        httpx_mock.add_response(
            method="GET",
            url="https://api.example.com/users/1",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )
        httpx_mock.add_response(
            method="GET",
            url="https://api.example.com/users",
            json=[{"id": 1, "name": "John", "email": "john@example.com"}],
        )

        client = APIClient()

        # Both should work
        response_get = client.users.get(id=1)
        response_list = client.users.list_all()

        assert response_get.status_code == 200
        assert response_list.status_code == 200
        assert len(response_list.data) == 1
