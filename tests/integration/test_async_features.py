"""Integration tests for async HTTP features."""

from typing import Annotated

import pytest
from pydantic import BaseModel
from pytest_httpx import HTTPXMock

from pydantic_httpx import (
    GET,
    POST,
    AsyncClient,
    BaseResource,
    ClientConfig,
    ResourceConfig,
    ResponseEndpoint,
)


class User(BaseModel):
    """Test model for User."""

    id: int
    name: str
    email: str


class UserResource(BaseResource):
    """Resource for testing async features."""

    resource_config = ResourceConfig(prefix="/users")

    get: Annotated[ResponseEndpoint[User], GET("/{id}")]
    list_all: Annotated[ResponseEndpoint[list[User]], GET("")]
    create: Annotated[ResponseEndpoint[User], POST("")]


class AsyncAPIClient(AsyncClient):
    """Test async client."""

    client_config = ClientConfig(base_url="https://api.example.com")

    users: UserResource


@pytest.mark.asyncio
class TestAsyncBasicOperations:
    """Tests for basic async HTTP operations."""

    async def test_async_get_single_user(self, httpx_mock: HTTPXMock) -> None:
        """Test async GET request for a single user."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="GET",
            json={"id": 1, "name": "John Doe", "email": "john@example.com"},
        )

        async with AsyncAPIClient() as client:
            response = await client.users.get(id=1)

            assert response.data.id == 1
            assert response.data.name == "John Doe"
            assert response.data.email == "john@example.com"
            assert response.status_code == 200

    async def test_async_list_users(self, httpx_mock: HTTPXMock) -> None:
        """Test async GET request for listing users."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="GET",
            json=[
                {"id": 1, "name": "John", "email": "john@example.com"},
                {"id": 2, "name": "Jane", "email": "jane@example.com"},
            ],
        )

        async with AsyncAPIClient() as client:
            response = await client.users.list_all()

            assert len(response.data) == 2
            assert response.data[0].name == "John"
            assert response.data[1].name == "Jane"

    async def test_async_create_user(self, httpx_mock: HTTPXMock) -> None:
        """Test async POST request to create a user."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="POST",
            json={"id": 3, "name": "Alice", "email": "alice@example.com"},
        )

        async with AsyncAPIClient() as client:
            response = await client.users.create(
                json={"name": "Alice", "email": "alice@example.com"}
            )

            assert response.data.id == 3
            assert response.data.name == "Alice"
            assert response.data.email == "alice@example.com"


class TestAsyncWithSyncComparison:
    """Tests to ensure same resource works with both sync and async clients."""

    @pytest.mark.asyncio
    async def test_same_resource_async(self, httpx_mock: HTTPXMock) -> None:
        """Test that the same resource definition works with async client."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="GET",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )

        async with AsyncAPIClient() as client:
            response = await client.users.get(id=1)
            assert response.data.name == "John"

    def test_same_resource_sync(self, httpx_mock: HTTPXMock) -> None:
        """Test that the same resource definition works with sync client."""
        from pydantic_httpx import Client

        class SyncAPIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: UserResource

        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="GET",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )

        with SyncAPIClient() as client:
            response = client.users.get(id=1)
            assert response.data.name == "John"


@pytest.mark.asyncio
class TestAsyncQueryParameters:
    """Tests for query parameters with async client."""

    async def test_async_query_params_no_model(self, httpx_mock: HTTPXMock) -> None:
        """Test async query parameters without validation."""

        class SearchResource(BaseResource):
            resource_config = ResourceConfig(prefix="/search")
            search: Annotated[ResponseEndpoint[list[User]], GET("")]

        class SearchClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            search: SearchResource

        httpx_mock.add_response(
            url="https://api.example.com/search?q=test&limit=5",
            method="GET",
            json=[{"id": 1, "name": "Test User", "email": "test@example.com"}],
        )

        async with SearchClient() as client:
            response = await client.search.search(q="test", limit=5)
            assert len(response.data) == 1
            assert response.data[0].name == "Test User"


@pytest.mark.asyncio
class TestAsyncContextManager:
    """Tests for async context manager behavior."""

    async def test_async_context_manager_closes_client(
        self, httpx_mock: HTTPXMock
    ) -> None:
        """Test that async context manager properly closes the client."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="GET",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )

        async with AsyncAPIClient() as client:
            await client.users.get(id=1)
            # Client should be usable inside the context

        # After exiting the context, the underlying httpx client should be closed
        # We can't directly test if it's closed, but this verifies no errors occur

    async def test_async_manual_close(self, httpx_mock: HTTPXMock) -> None:
        """Test manual closing of async client."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="GET",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )

        client = AsyncAPIClient()
        await client.users.get(id=1)
        await client.close()
        # Verify no errors when manually closing
