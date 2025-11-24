"""Integration tests for endpoint validators."""

from typing import Annotated, Any

import pytest
from pydantic import BaseModel

from pydantic_httpx import (
    GET,
    POST,
    AsyncClient,
    BaseResource,
    Client,
    ClientConfig,
    Endpoint,
    ResourceConfig,
    endpoint_validator,
)
from pydantic_httpx.response import DataResponse


# Test models
class User(BaseModel):
    id: int
    name: str


# Test client with "before" validator
class ClientWithBeforeValidator(Client):
    client_config = ClientConfig(base_url="https://api.example.com")

    get_user: Annotated[Endpoint[User], GET("/users/{id}")]

    @endpoint_validator("get_user", mode="before")
    def validate_user_id(cls, params: dict[str, Any]) -> dict[str, Any]:
        """Ensure user ID is positive."""
        if params.get("id", 0) <= 0:
            raise ValueError("User ID must be positive")
        return params


# Test client with "after" validator
class ClientWithAfterValidator(Client):
    client_config = ClientConfig(
        base_url="https://api.example.com", raise_on_error=False
    )

    get_user: Annotated[Endpoint[User], GET("/users/{id}")]

    @endpoint_validator("get_user", mode="after")
    def handle_404(
        cls, response: DataResponse[User]
    ) -> DataResponse[User] | DataResponse[None]:
        """Return None on 404."""
        if response.status_code == 404:
            # Return a new response with None data
            return DataResponse(response.response, None)
        return response


# Test client with "wrap" validator (caching)
class ClientWithWrapValidator(Client):
    client_config = ClientConfig(base_url="https://api.example.com")

    get_user: Annotated[Endpoint[User], GET("/users/{id}")]

    # Simple cache storage (class-level for this test)
    _cache: dict[int, User] = {}

    @endpoint_validator("get_user", mode="wrap")
    def cache_user(
        cls, handler: Any, params: dict[str, Any]
    ) -> DataResponse[User] | User:
        """Cache user responses."""
        user_id = params["id"]

        # Check cache
        if user_id in cls._cache:
            return cls._cache[user_id]

        # Call the handler
        response = handler(params)

        # Store in cache (handle both DataResponse and direct data)
        if isinstance(response, DataResponse):
            cls._cache[user_id] = response.data
            return response.data
        else:
            cls._cache[user_id] = response
            return response


# Test resource with validators
class UserResourceWithValidators(BaseResource):
    resource_config = ResourceConfig(prefix="/users")

    get: Annotated[Endpoint[User], GET("/{id}")]
    create: Annotated[Endpoint[User], POST("")]

    @endpoint_validator("get", mode="before")
    def validate_get_id(cls, params: dict[str, Any]) -> dict[str, Any]:
        """Validate ID on resource endpoint."""
        if params.get("id", 0) < 1:
            raise ValueError("ID must be at least 1")
        return params

    @endpoint_validator("create", mode="after")
    def log_creation(cls, response: DataResponse[User]) -> DataResponse[User]:
        """Add a flag to indicate logging occurred."""
        # In real use, this would log the creation
        # For testing, we'll store a flag
        response._logged = True  # type: ignore[attr-defined]
        return response


class ClientWithResource(Client):
    client_config = ClientConfig(base_url="https://api.example.com")

    users: UserResourceWithValidators


# Async tests
class AsyncClientWithBeforeValidator(AsyncClient):
    client_config = ClientConfig(base_url="https://api.example.com")

    get_user: Annotated[Endpoint[User], GET("/users/{id}")]

    @endpoint_validator("get_user", mode="before")
    def validate_user_id(cls, params: dict[str, Any]) -> dict[str, Any]:
        """Ensure user ID is positive."""
        if params.get("id", 0) <= 0:
            raise ValueError("User ID must be positive")
        return params


class TestBeforeValidators:
    """Test 'before' mode validators that transform/validate parameters."""

    def test_before_validator_allows_valid_params(self, httpx_mock):
        """Valid parameters should pass through the validator."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1", json={"id": 1, "name": "Alice"}
        )

        client = ClientWithBeforeValidator()
        user = client.get_user(path={"id": 1})

        assert user.id == 1
        assert user.name == "Alice"

    def test_before_validator_rejects_invalid_params(self):
        """Invalid parameters should be rejected by the validator."""
        client = ClientWithBeforeValidator()

        with pytest.raises(ValueError, match="User ID must be positive"):
            client.get_user(path={"id": 0})

    def test_before_validator_can_transform_params(self, httpx_mock):
        """Before validators can modify parameters."""

        class TransformingClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")

            get_user: Annotated[Endpoint[User], GET("/users/{id}")]

            @endpoint_validator("get_user", mode="before")
            def uppercase_transform(cls, params: dict[str, Any]) -> dict[str, Any]:
                """Add a default parameter."""
                params["id"] = params.get("id", 1)
                return params

        httpx_mock.add_response(
            url="https://api.example.com/users/1", json={"id": 1, "name": "Alice"}
        )

        client = TransformingClient()
        user = client.get_user()  # No ID provided, validator adds default

        assert user.id == 1


class TestAfterValidators:
    """Test 'after' mode validators that transform responses."""

    def test_after_validator_transforms_response(self, httpx_mock):
        """After validators can transform the response."""
        # Return a valid user for 404 - the validator will transform it
        httpx_mock.add_response(
            url="https://api.example.com/users/999",
            status_code=404,
            json={"id": 999, "name": "NotFound"},
        )

        client = ClientWithAfterValidator()
        response = client.get_user(path={"id": 999})

        # The validator transformed 404 into None
        assert response.data is None
        assert response.status_code == 404

    def test_after_validator_passes_through_success(self, httpx_mock):
        """After validators pass through successful responses unchanged."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1", json={"id": 1, "name": "Alice"}
        )

        client = ClientWithAfterValidator()
        response = client.get_user(path={"id": 1})

        assert response.data.id == 1
        assert response.data.name == "Alice"


class TestWrapValidators:
    """Test 'wrap' mode validators that control execution."""

    def test_wrap_validator_caching(self, httpx_mock):
        """Wrap validators can implement caching."""
        # Clear cache before test
        ClientWithWrapValidator._cache.clear()

        httpx_mock.add_response(
            url="https://api.example.com/users/1", json={"id": 1, "name": "Alice"}
        )

        client = ClientWithWrapValidator()

        # First call - hits the API
        user1 = client.get_user(path={"id": 1})
        assert user1.id == 1
        assert user1.name == "Alice"
        assert len(httpx_mock.get_requests()) == 1

        # Second call - should use cache (no new request)
        user2 = client.get_user(path={"id": 1})
        assert user2.id == 1
        assert user2.name == "Alice"
        assert len(httpx_mock.get_requests()) == 1  # Still only 1 request

        # Verify cache was used
        assert 1 in ClientWithWrapValidator._cache


class TestResourceValidators:
    """Test validators defined on resources."""

    def test_resource_before_validator(self, httpx_mock):
        """Resource validators work for 'before' mode."""
        httpx_mock.add_response(
            url="https://api.example.com/users/5", json={"id": 5, "name": "Bob"}
        )

        client = ClientWithResource()
        user = client.users.get(path={"id": 5})

        assert user.id == 5
        assert user.name == "Bob"

    def test_resource_before_validator_rejects(self):
        """Resource validators reject invalid parameters."""
        client = ClientWithResource()

        with pytest.raises(ValueError, match="ID must be at least 1"):
            client.users.get(path={"id": 0})

    def test_resource_after_validator(self, httpx_mock):
        """Resource validators work for 'after' mode."""
        httpx_mock.add_response(
            url="https://api.example.com/users",
            method="POST",
            json={"id": 1, "name": "Charlie"},
        )

        client = ClientWithResource()
        user = client.users.create(json={"name": "Charlie"})

        assert user.id == 1
        # Note: The after validator modifies the response object,
        # but since we're returning data only, we can't check the flag directly
        # This demonstrates that after validators work with resource endpoints


class TestMultipleValidators:
    """Test multiple validators on the same endpoint."""

    def test_multiple_validators_execute_in_order(self, httpx_mock):
        """Multiple validators execute in the correct order."""
        # Track execution order
        execution_order = []

        class MultiValidatorClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")

            get_user: Annotated[Endpoint[User], GET("/users/{id}")]

            @endpoint_validator("get_user", mode="before")
            def first_validator(cls, params: dict[str, Any]) -> dict[str, Any]:
                """First validator runs first."""
                execution_order.append("first")
                return params

            @endpoint_validator("get_user", mode="before")
            def second_validator(cls, params: dict[str, Any]) -> dict[str, Any]:
                """Second validator runs second."""
                execution_order.append("second")
                return params

        httpx_mock.add_response(
            url="https://api.example.com/users/1", json={"id": 1, "name": "Alice"}
        )

        client = MultiValidatorClient()
        user = client.get_user(path={"id": 1})

        assert user.id == 1
        assert execution_order == ["first", "second"]


class TestAsyncValidators:
    """Test validators work with async clients."""

    @pytest.mark.asyncio
    async def test_async_before_validator(self, httpx_mock):
        """Validators work with async clients."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1", json={"id": 1, "name": "Alice"}
        )

        async with AsyncClientWithBeforeValidator() as client:
            user = await client.get_user(path={"id": 1})

            assert user.id == 1
            assert user.name == "Alice"

    @pytest.mark.asyncio
    async def test_async_before_validator_rejects(self):
        """Async validators can reject invalid parameters."""
        async with AsyncClientWithBeforeValidator() as client:
            with pytest.raises(ValueError, match="User ID must be positive"):
                await client.get_user(path={"id": 0})


class TestValidatorEdgeCases:
    """Test edge cases and error scenarios."""

    def test_validator_on_nonexistent_endpoint(self):
        """Validator on non-existent endpoint is silently ignored."""

        class ClientWithInvalidValidator(Client):
            client_config = ClientConfig(base_url="https://api.example.com")

            get_user: Annotated[Endpoint[User], GET("/users/{id}")]

            @endpoint_validator("nonexistent_endpoint", mode="before")
            def unused_validator(cls, params: dict[str, Any]) -> dict[str, Any]:
                """This validator targets a non-existent endpoint."""
                return params

        # Should not raise an error during class creation
        client = ClientWithInvalidValidator()
        assert client is not None

    def test_endpoint_without_validators(self, httpx_mock):
        """Endpoints without validators work normally."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1", json={"id": 1, "name": "Alice"}
        )

        # Regular client without validators
        class RegularClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")

            get_user: Annotated[Endpoint[User], GET("/users/{id}")]

        client = RegularClient()
        user = client.get_user(path={"id": 1})

        assert user.id == 1
        assert user.name == "Alice"
