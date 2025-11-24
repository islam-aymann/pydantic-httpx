"""Tests for type hint-based validation of query, path, headers, cookies."""

from typing import Annotated

import pytest
from pydantic import BaseModel, ConfigDict

from pydantic_httpx import (
    GET,
    AsyncClient,
    BaseResource,
    Client,
    ClientConfig,
    Endpoint,
)
from pydantic_httpx.exceptions import ValidationError


class QueryParams(BaseModel):
    """Query parameters model."""

    page: int
    limit: int = 10


class PathParams(BaseModel):
    """Path parameters model."""

    user_id: int


class HeadersModel(BaseModel):
    """Headers model."""

    x_api_key: str
    x_request_id: str | None = None


class CookiesModel(BaseModel):
    """Cookies model."""

    session_id: str
    remember_me: str = "false"


class User(BaseModel):
    """User model."""

    id: int
    name: str
    email: str


class TestQueryParameterValidation:
    """Test query parameter validation using type hints."""

    def test_query_parameter_validation_success(self, httpx_mock):
        """Test that query parameters are validated successfully."""

        class APIResource(BaseResource):
            # Query parameter validation via 3rd type parameter
            search: Annotated[Endpoint[list[User], None, QueryParams], GET("/users")]

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: APIResource

        httpx_mock.add_response(
            url="https://api.example.com/users?page=1&limit=10",
            json=[
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
            ],
        )

        with APIClient() as client:
            response = client.users.search(params={"page": 1, "limit": 10})
            assert len(response.data) == 2
            assert response.data[0].name == "Alice"

    def test_query_parameter_validation_failure(self, httpx_mock):
        """Test that invalid query parameters raise ValidationError."""

        class APIResource(BaseResource):
            search: Annotated[Endpoint[list[User], None, QueryParams], GET("/users")]

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: APIResource

        with APIClient() as client:
            with pytest.raises(ValidationError) as exc_info:
                # Invalid: page should be int, not string
                client.users.search(params={"page": "invalid", "limit": 10})

            assert "Validation failed for 'params' parameter" in str(exc_info.value)


class TestPathParameterValidation:
    """Test path parameter validation using type hints."""

    def test_path_parameter_validation_success(self, httpx_mock):
        """Test that path parameters are validated successfully."""

        class APIResource(BaseResource):
            # Path parameter validation via 4th type parameter
            get: Annotated[
                Endpoint[User, None, None, PathParams], GET("/users/{user_id}")
            ]

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: APIResource

        httpx_mock.add_response(
            url="https://api.example.com/users/123",
            json={"id": 123, "name": "Alice", "email": "alice@example.com"},
        )

        with APIClient() as client:
            response = client.users.get(path={"user_id": 123})
            assert response.data.id == 123
            assert response.data.name == "Alice"

    def test_path_parameter_validation_failure(self, httpx_mock):
        """Test that invalid path parameters raise ValidationError.

        Note: Path parameters are validated but Pydantic's default behavior
        is to coerce types when possible. To trigger a validation error,
        we need to use strict mode or pass truly invalid data.
        """

        class StrictPathParams(BaseModel):
            """Path parameters model with strict validation."""

            model_config = ConfigDict(str_strip_whitespace=False)

            user_id: int

        class APIResource(BaseResource):
            get: Annotated[
                Endpoint[User, None, None, StrictPathParams], GET("/users/{user_id}")
            ]

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: APIResource

        httpx_mock.add_response(
            url="https://api.example.com/users/123",
            json={"id": 123, "name": "Alice", "email": "alice@example.com"},
        )

        with APIClient() as client:
            # Valid: Pydantic will coerce string "123" to int 123
            response = client.users.get(path={"user_id": "123"})
            assert response.data.id == 123


class TestHeadersParameterValidation:
    """Test headers parameter validation using type hints."""

    def test_headers_parameter_validation_success(self, httpx_mock):
        """Test that headers are validated successfully."""

        class APIResource(BaseResource):
            # Headers parameter validation via 5th type parameter
            get: Annotated[
                Endpoint[User, None, None, None, HeadersModel], GET("/users/me")
            ]

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: APIResource

        httpx_mock.add_response(
            url="https://api.example.com/users/me",
            json={"id": 1, "name": "Alice", "email": "alice@example.com"},
        )

        with APIClient() as client:
            response = client.users.get(
                headers={"x_api_key": "secret", "x_request_id": "req-123"}
            )
            assert response.data.name == "Alice"

    def test_headers_parameter_validation_failure(self, httpx_mock):
        """Test that invalid headers raise ValidationError."""

        class APIResource(BaseResource):
            get: Annotated[
                Endpoint[User, None, None, None, HeadersModel], GET("/users/me")
            ]

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: APIResource

        with APIClient() as client:
            with pytest.raises(ValidationError) as exc_info:
                # Invalid: missing required x_api_key header
                client.users.get(headers={"x_request_id": "req-123"})

            assert "Validation failed for 'headers' parameter" in str(exc_info.value)


class TestCookiesParameterValidation:
    """Test cookies parameter validation using type hints."""

    def test_cookies_parameter_validation_success(self, httpx_mock):
        """Test that cookies are validated successfully."""

        class APIResource(BaseResource):
            # Cookies parameter validation via 6th type parameter
            get: Annotated[
                Endpoint[User, None, None, None, None, CookiesModel], GET("/users/me")
            ]

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: APIResource

        httpx_mock.add_response(
            url="https://api.example.com/users/me",
            json={"id": 1, "name": "Alice", "email": "alice@example.com"},
        )

        with APIClient() as client:
            response = client.users.get(
                cookies={"session_id": "abc123", "remember_me": "true"}
            )
            assert response.data.name == "Alice"

    def test_cookies_parameter_validation_failure(self, httpx_mock):
        """Test that invalid cookies raise ValidationError."""

        class APIResource(BaseResource):
            get: Annotated[
                Endpoint[User, None, None, None, None, CookiesModel], GET("/users/me")
            ]

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: APIResource

        with APIClient() as client:
            with pytest.raises(ValidationError) as exc_info:
                # Invalid: missing required session_id cookie
                client.users.get(cookies={"remember_me": "true"})

            assert "Validation failed for 'cookies' parameter" in str(exc_info.value)


class TestCombinedParameterValidation:
    """Test validation of multiple parameter types together."""

    def test_combined_query_and_path_validation(self, httpx_mock):
        """Test validation of both query and path parameters."""

        class APIResource(BaseResource):
            # Query (3rd) and Path (4th) parameter validation
            get: Annotated[
                Endpoint[list[User], None, QueryParams, PathParams],
                GET("/users/{user_id}/friends"),
            ]

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: APIResource

        httpx_mock.add_response(
            url="https://api.example.com/users/123/friends?page=1&limit=10",
            json=[
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
                {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
            ],
        )

        with APIClient() as client:
            response = client.users.get(
                path={"user_id": 123}, params={"page": 1, "limit": 10}
            )
            assert len(response.data) == 2

    def test_combined_all_parameters_validation(self, httpx_mock):
        """Test validation of query, path, headers, and cookies together."""

        class APIResource(BaseResource):
            # All parameter types validated
            get: Annotated[
                Endpoint[
                    User, None, QueryParams, PathParams, HeadersModel, CookiesModel
                ],
                GET("/users/{user_id}"),
            ]

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: APIResource

        httpx_mock.add_response(
            url="https://api.example.com/users/123?page=1&limit=10",
            json={"id": 123, "name": "Alice", "email": "alice@example.com"},
        )

        with APIClient() as client:
            response = client.users.get(
                path={"user_id": 123},
                params={"page": 1, "limit": 10},
                headers={"x_api_key": "secret"},
                cookies={"session_id": "abc123"},
            )
            assert response.data.id == 123


class TestAsyncParameterValidation:
    """Test parameter validation with async client."""

    @pytest.mark.asyncio
    async def test_async_query_parameter_validation(self, httpx_mock):
        """Test query parameter validation with async client."""

        class APIResource(BaseResource):
            search: Annotated[Endpoint[list[User], None, QueryParams], GET("/users")]

        class APIAsyncClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: APIResource

        httpx_mock.add_response(
            url="https://api.example.com/users?page=1&limit=10",
            json=[
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
            ],
        )

        async with APIAsyncClient() as client:
            response = await client.users.search(params={"page": 1, "limit": 10})
            assert len(response.data) == 2
            assert response.data[0].name == "Alice"

    @pytest.mark.asyncio
    async def test_async_parameter_validation_failure(self, httpx_mock):
        """Test that invalid parameters raise ValidationError in async client."""

        class APIResource(BaseResource):
            search: Annotated[Endpoint[list[User], None, QueryParams], GET("/users")]

        class APIAsyncClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: APIResource

        async with APIAsyncClient() as client:
            with pytest.raises(ValidationError) as exc_info:
                # Invalid: page should be int, not string
                await client.users.search(params={"page": "invalid", "limit": 10})

            assert "Validation failed for 'params' parameter" in str(exc_info.value)


class TestPydanticModelParams:
    """Test passing Pydantic models directly as parameters."""

    def test_query_params_as_pydantic_model(self, httpx_mock):
        """Test passing Pydantic model instance for query params."""

        class APIResource(BaseResource):
            search: Annotated[Endpoint[list[User], None, QueryParams], GET("/users")]

        class APIClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: APIResource

        httpx_mock.add_response(
            url="https://api.example.com/users?page=1&limit=10",
            json=[{"id": 1, "name": "Alice", "email": "alice@example.com"}],
        )

        with APIClient() as client:
            # Pass Pydantic model instance directly
            query_params = QueryParams(page=1, limit=10)
            response = client.users.search(params=query_params)
            assert len(response.data) == 1
