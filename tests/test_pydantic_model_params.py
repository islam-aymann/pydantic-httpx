"""Test that endpoints accept Pydantic models directly as parameters."""

from __future__ import annotations

from typing import Annotated

import pytest
from pydantic import BaseModel

from pydantic_httpx import (
    POST,
    AsyncClient,
    BaseResource,
    Client,
    ClientConfig,
    Endpoint,
    ResourceConfig,
)


class CreateUserRequest(BaseModel):
    """Request model for creating a user."""

    name: str
    email: str
    age: int | None = None


class User(BaseModel):
    """User response model."""

    id: int
    name: str
    email: str
    age: int | None = None


class UserResource(BaseResource):
    """User resource with endpoint that accepts request model."""

    resource_config = ResourceConfig(prefix="/users")

    create: Annotated[Endpoint[User, CreateUserRequest], POST("")]


class TestSyncClientPydanticModelParams:
    """Test sync client accepting Pydantic models as parameters."""

    def test_accepts_dict_parameter(self, httpx_mock):
        """Test endpoint accepts dict for data parameter."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.example.com/users",
            json={"id": 1, "name": "John", "email": "john@example.com", "age": 30},
        )

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: UserResource

        client = APIClient()
        response = client.users.create(
            data={"name": "John", "email": "john@example.com", "age": 30}
        )

        assert response.data.id == 1
        assert response.data.name == "John"
        assert response.data.email == "john@example.com"

    def test_accepts_pydantic_model_parameter(self, httpx_mock):
        """Test endpoint accepts Pydantic model for data parameter."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.example.com/users",
            json={"id": 2, "name": "Jane", "email": "jane@example.com", "age": 25},
        )

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: UserResource

        client = APIClient()

        # Pass Pydantic model directly
        request_model = CreateUserRequest(name="Jane", email="jane@example.com", age=25)
        response = client.users.create(data=request_model)

        assert response.data.id == 2
        assert response.data.name == "Jane"
        assert response.data.email == "jane@example.com"

    def test_accepts_different_pydantic_model_converts(self, httpx_mock):
        """Test endpoint converts different Pydantic model to request model."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.example.com/users",
            json={"id": 3, "name": "Bob", "email": "bob@example.com"},
        )

        class DifferentModel(BaseModel):
            name: str
            email: str

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: UserResource

        client = APIClient()

        # Pass different Pydantic model - should convert via dict
        different_model = DifferentModel(name="Bob", email="bob@example.com")
        response = client.users.create(data=different_model)

        assert response.data.id == 3
        assert response.data.name == "Bob"
        assert response.data.email == "bob@example.com"


class TestAsyncClientPydanticModelParams:
    """Test async client accepting Pydantic models as parameters."""

    @pytest.mark.asyncio
    async def test_accepts_dict_parameter(self, httpx_mock):
        """Test endpoint accepts dict for data parameter."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.example.com/users",
            json={"id": 1, "name": "John", "email": "john@example.com", "age": 30},
        )

        class APIClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: UserResource

        async with APIClient() as client:
            response = await client.users.create(
                data={"name": "John", "email": "john@example.com", "age": 30}
            )

            assert response.data.id == 1
            assert response.data.name == "John"

    @pytest.mark.asyncio
    async def test_accepts_pydantic_model_parameter(self, httpx_mock):
        """Test endpoint accepts Pydantic model for data parameter."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.example.com/users",
            json={"id": 2, "name": "Jane", "email": "jane@example.com", "age": 25},
        )

        class APIClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: UserResource

        async with APIClient() as client:
            request_model = CreateUserRequest(
                name="Jane", email="jane@example.com", age=25
            )
            response = await client.users.create(data=request_model)

            assert response.data.id == 2
            assert response.data.name == "Jane"

    @pytest.mark.asyncio
    async def test_accepts_different_pydantic_model_converts(self, httpx_mock):
        """Test endpoint converts different Pydantic model to request model."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.example.com/users",
            json={"id": 3, "name": "Bob", "email": "bob@example.com"},
        )

        class DifferentModel(BaseModel):
            name: str
            email: str

        class APIClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: UserResource

        async with APIClient() as client:
            different_model = DifferentModel(name="Bob", email="bob@example.com")
            response = await client.users.create(data=different_model)

            assert response.data.id == 3
            assert response.data.name == "Bob"
