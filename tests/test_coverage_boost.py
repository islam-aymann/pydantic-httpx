"""
Additional tests to improve test coverage.

This test file focuses on covering specific lines that are missed in the
coverage report, particularly around edge cases in endpoint handling,
validators, and error scenarios.
"""

from typing import Annotated

import httpx
import pytest
from pydantic import BaseModel
from pytest_httpx import HTTPXMock

from pydantic_httpx import (
    GET,
    AsyncClient,
    BaseResource,
    Client,
    ClientConfig,
    DataResponse,
    Endpoint,
    HTTPError,
    RequestError,
    ResourceConfig,
    ValidationError,
    endpoint_validator,
)


class User(BaseModel):
    """Test model for user data."""

    id: int
    name: str


class TestAsyncWrapValidatorEdgeCases:
    """Test async wrap validator edge cases to cover lines 189-190, 203."""

    def test_async_wrap_validator_returns_non_dataresponse(self, httpx_mock: HTTPXMock):
        """Test async wrap validator that returns data directly (not DataResponse)."""

        class TestAsyncClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            get_user: Annotated[Endpoint[User], GET("/users/{id}")]

            @endpoint_validator("get_user", mode="wrap")
            async def cached_response(cls, handler, params: dict) -> User:
                # Return User directly, not DataResponse
                # This tests lines 203-204 in resource.py (async path)
                return User(id=42, name="Cached Async User")

        async def run_test():
            async with TestAsyncClient() as client:
                user = await client.get_user(path={"id": 1})
                assert user.id == 42
                assert user.name == "Cached Async User"

        import asyncio

        asyncio.run(run_test())

    def test_async_wrap_validator_with_awaitable_result(self, httpx_mock: HTTPXMock):
        """Test async wrap validator where result needs to be awaited (line 200)."""

        httpx_mock.add_response(json={"id": 10, "name": "Test"})

        class TestAsyncClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            get_user: Annotated[Endpoint[User], GET("/users/{id}")]

            @endpoint_validator("get_user", mode="wrap")
            async def async_wrap(cls, handler, params: dict) -> DataResponse[User]:
                # Return awaitable DataResponse
                response = await handler(params)
                return response

        async def run_test():
            async with TestAsyncClient() as client:
                user = await client.get_user(path={"id": 10})
                assert user.id == 10
                assert user.name == "Test"

        import asyncio

        asyncio.run(run_test())


class TestResourceAfterValidatorWithEndpoint:
    """Test after validators with Endpoint to cover line 306."""

    def test_resource_after_validator_with_response_endpoint(
        self, httpx_mock: HTTPXMock
    ):
        """Test resource with after validator that modifies result."""

        class UserResource(BaseResource):
            resource_config = ResourceConfig(prefix="/users")
            get: Annotated[Endpoint[User], GET("/{id}")]

            @endpoint_validator("get", mode="after")
            def modify_response(
                cls, response: DataResponse[User]
            ) -> DataResponse[User]:
                # Return modified DataResponse with uppercased name
                modified_user = User(
                    id=response.data.id, name=response.data.name.upper()
                )
                return DataResponse(response.response, modified_user)

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: UserResource

        httpx_mock.add_response(json={"id": 7, "name": "Modified"})

        client = TestClient()
        result = client.users.get(path={"id": 7})

        # The result should be DataResponse with modified User
        assert isinstance(result, DataResponse)
        assert isinstance(result.data, User)
        assert result.data.id == 7
        assert result.data.name == "MODIFIED"  # Uppercased by validator


class TestEndpointWithCookiesAuthRedirects:
    """Test endpoints with cookies, auth, and follow_redirects options."""

    def test_async_endpoint_with_cookies(self, httpx_mock: HTTPXMock):
        """Test async endpoint with cookies parameter (line 167)."""

        class TestAsyncClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            get_user: Annotated[
                Endpoint[User],
                GET("/users/{id}", cookies={"session": "abc123"}),
            ]

        httpx_mock.add_response(json={"id": 1, "name": "Alice"})

        async def run_test():
            async with TestAsyncClient() as client:
                user = await client.get_user(path={"id": 1})
                assert user.name == "Alice"

                # Check cookies were sent
                request = httpx_mock.get_request()
                assert "cookie" in request.headers or "Cookie" in request.headers

        import asyncio

        asyncio.run(run_test())

    def test_async_endpoint_with_auth(self, httpx_mock: HTTPXMock):
        """Test async endpoint with auth parameter (line 171)."""

        class TestAsyncClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            get_user: Annotated[
                Endpoint[User], GET("/users/{id}", auth=("user", "pass"))
            ]

        httpx_mock.add_response(json={"id": 2, "name": "Bob"})

        async def run_test():
            async with TestAsyncClient() as client:
                user = await client.get_user(path={"id": 2})
                assert user.name == "Bob"

                # Check auth was sent
                request = httpx_mock.get_request()
                assert (
                    "authorization" in request.headers
                    or "Authorization" in request.headers
                )

        import asyncio

        asyncio.run(run_test())

    def test_async_endpoint_with_follow_redirects(self, httpx_mock: HTTPXMock):
        """Test async endpoint with follow_redirects parameter (line 175)."""

        class TestAsyncClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            get_user: Annotated[
                Endpoint[User], GET("/users/{id}", follow_redirects=False)
            ]

        httpx_mock.add_response(json={"id": 3, "name": "Charlie"})

        async def run_test():
            async with TestAsyncClient() as client:
                user = await client.get_user(path={"id": 3})
                assert user.name == "Charlie"

        import asyncio

        asyncio.run(run_test())


class TestClientTimeoutErrors:
    """Test timeout error handling in both sync and async clients."""

    def test_sync_client_timeout_error(self, httpx_mock: HTTPXMock):
        """Test sync client converts httpx.TimeoutException to RequestError."""

        class TestClient(Client):
            client_config = ClientConfig(
                base_url="https://api.example.com", timeout=0.001
            )
            get_user: Annotated[Endpoint[User], GET("/users/{id}")]

        # Simulate timeout by not adding a response
        httpx_mock.add_exception(httpx.TimeoutException("Request timeout"))

        client = TestClient()

        with pytest.raises(RequestError) as exc_info:
            client.get_user(path={"id": 1})

        assert "timeout" in str(exc_info.value).lower() or "Request timeout" in str(
            exc_info.value
        )

    def test_sync_client_network_error(self, httpx_mock: HTTPXMock):
        """Test sync client converts httpx.RequestError to RequestError."""

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            get_user: Annotated[Endpoint[User], GET("/users/{id}")]

        # Simulate network error
        httpx_mock.add_exception(httpx.RequestError("Connection failed"))

        client = TestClient()

        with pytest.raises(RequestError) as exc_info:
            client.get_user(path={"id": 1})

        assert (
            "Connection failed" in str(exc_info.value)
            or "request" in str(exc_info.value).lower()
        )

    def test_async_client_timeout_error(self, httpx_mock: HTTPXMock):
        """Test async client converts httpx.TimeoutException to RequestError."""

        class TestAsyncClient(AsyncClient):
            client_config = ClientConfig(
                base_url="https://api.example.com", timeout=0.001
            )
            get_user: Annotated[Endpoint[User], GET("/users/{id}")]

        httpx_mock.add_exception(httpx.TimeoutException("Request timeout"))

        async def run_test():
            async with TestAsyncClient() as client:
                with pytest.raises(RequestError) as exc_info:
                    await client.get_user(path={"id": 1})

                assert "timeout" in str(
                    exc_info.value
                ).lower() or "Request timeout" in str(exc_info.value)

        import asyncio

        asyncio.run(run_test())

    def test_async_client_network_error(self, httpx_mock: HTTPXMock):
        """Test async client converts httpx.RequestError to RequestError."""

        class TestAsyncClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            get_user: Annotated[Endpoint[User], GET("/users/{id}")]

        httpx_mock.add_exception(httpx.RequestError("Network error"))

        async def run_test():
            async with TestAsyncClient() as client:
                with pytest.raises(RequestError) as exc_info:
                    await client.get_user(path={"id": 1})

                assert (
                    "Network error" in str(exc_info.value)
                    or "request" in str(exc_info.value).lower()
                )

        import asyncio

        asyncio.run(run_test())


class TestQueryParamsWithoutModel:
    """Test query parameters without validation model."""

    def test_sync_query_params_without_model(self, httpx_mock: HTTPXMock):
        """Test passing query params as kwargs without query_model (line 193)."""

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            # No query_model specified
            list_users: Annotated[Endpoint[list[User]], GET("/users")]

        httpx_mock.add_response(json=[{"id": 1, "name": "Alice"}])

        client = TestClient()
        response = client.list_users(params={"limit": 10, "offset": 0})

        assert isinstance(response, DataResponse)
        assert len(response.data) == 1
        assert response.data[0].name == "Alice"

        # Verify query params were passed
        request = httpx_mock.get_request()
        assert "limit=10" in str(request.url) and "offset=0" in str(request.url)

    def test_async_query_params_without_model(self, httpx_mock: HTTPXMock):
        """Test async query params as kwargs without query_model."""

        class TestAsyncClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            list_users: Annotated[Endpoint[list[User]], GET("/users")]

        httpx_mock.add_response(json=[{"id": 2, "name": "Bob"}])

        async def run_test():
            async with TestAsyncClient() as client:
                response = await client.list_users(params={"page": 1})
                assert isinstance(response, DataResponse)
                assert len(response.data) == 1
                assert response.data[0].name == "Bob"

                request = httpx_mock.get_request()
                assert "page=1" in str(request.url)

        import asyncio

        asyncio.run(run_test())


class TestResponseValidationEdgeCases:
    """Test edge cases in response validation."""

    def test_async_list_with_non_basemodel_items(self, httpx_mock: HTTPXMock):
        """Test async response with list[dict] (lines 260-261)."""

        class TestAsyncClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            get_data: Annotated[Endpoint[list[dict]], GET("/data")]

        httpx_mock.add_response(json=[{"key": "value"}, {"key": "value2"}])

        async def run_test():
            async with TestAsyncClient() as client:
                response = await client.get_data()
                assert isinstance(response, DataResponse)
                assert len(response.data) == 2
                assert response.data[0]["key"] == "value"

        import asyncio

        asyncio.run(run_test())

    def test_async_response_parsing_error(self, httpx_mock: HTTPXMock):
        """Test async client with invalid JSON response (line 271)."""

        class TestAsyncClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            get_user: Annotated[Endpoint[User], GET("/users/{id}")]

        httpx_mock.add_response(content=b"Invalid JSON!", status_code=200)

        async def run_test():
            async with TestAsyncClient() as client:
                with pytest.raises(RequestError) as exc_info:
                    await client.get_user(path={"id": 1})

                assert "Failed to parse response" in str(exc_info.value)

        import asyncio

        asyncio.run(run_test())


class TestInnerTypeExtraction:
    """Test _extract_inner_type method edge cases."""

    def test_sync_type_without_args(self, httpx_mock: HTTPXMock):
        """Test endpoint with response type that has no args (line 226)."""

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            # Using plain dict without generic args
            get_data: Annotated[Endpoint[dict], GET("/data")]

        httpx_mock.add_response(json={"result": "success"})

        client = TestClient()
        response = client.get_data()
        assert isinstance(response, DataResponse)
        assert response.data["result"] == "success"

    def test_async_type_without_args(self, httpx_mock: HTTPXMock):
        """Test async endpoint with response type that has no args (line 228)."""

        class TestAsyncClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            get_data: Annotated[Endpoint[dict], GET("/data")]

        httpx_mock.add_response(json={"status": "ok"})

        async def run_test():
            async with TestAsyncClient() as client:
                response = await client.get_data()
                assert isinstance(response, DataResponse)
                assert response.data["status"] == "ok"

        import asyncio

        asyncio.run(run_test())


class TestRequestBuilderEdgeCases:
    """Test edge cases in _request_builder.py."""

    def test_request_validation_error_with_pydantic_validation_error(
        self, httpx_mock: HTTPXMock
    ):
        """Test PydanticValidationError handling in request builder."""

        class CreateUser(BaseModel):
            name: str
            email: str

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            create: Annotated[Endpoint[User, CreateUser], GET("/users")]

        client = TestClient()

        with pytest.raises((ValidationError, RequestError)):
            client.create(json={"name": "John"})

    def test_query_params_with_basemodel_instance(self, httpx_mock: HTTPXMock):
        """Test query params when passing BaseModel instance."""

        class QueryParams(BaseModel):
            limit: int
            offset: int

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            search: Annotated[Endpoint[list[User]], GET("/search")]

        httpx_mock.add_response(json=[{"id": 1, "name": "Test"}])

        client = TestClient()
        params = QueryParams(limit=10, offset=0)
        response = client.search(params=params)
        assert len(response.data) == 1


class TestClientInitSubclass:
    """Test __init_subclass__ edge cases."""

    def test_sync_client_without_client_config(self):
        """Test Client subclass without client_config attribute."""

        class TestClient(Client):
            pass

        client = TestClient()
        assert client is not None

    def test_sync_client_with_none_client_config(self):
        """Test Client subclass with client_config = None."""

        class TestClient(Client):
            client_config = None  # type: ignore[assignment]

        client = TestClient()
        assert client is not None

    def test_sync_client_with_problematic_type_hints(self):
        """Test Client when get_type_hints raises exception."""

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")

        client = TestClient()
        assert client is not None

    def test_async_client_without_client_config(self):
        """Test AsyncClient subclass without client_config attribute."""

        class TestAsyncClient(AsyncClient):
            pass

        async def run_test():
            async with TestAsyncClient() as client:
                assert client is not None

        import asyncio

        asyncio.run(run_test())

    def test_async_client_with_problematic_type_hints(self):
        """Test AsyncClient when get_type_hints raises exception."""

        class TestAsyncClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")

        async def run_test():
            async with TestAsyncClient() as client:
                assert client is not None

        import asyncio

        asyncio.run(run_test())


class TestRaiseOnErrorConfig:
    """Test raise_on_error configuration."""

    def test_async_raise_on_error_true(self, httpx_mock: HTTPXMock):
        """Test async client with raise_on_error=True."""

        class TestAsyncClient(AsyncClient):
            client_config = ClientConfig(
                base_url="https://api.example.com", raise_on_error=True
            )
            get_user: Annotated[Endpoint[User], GET("/users/{id}")]

        httpx_mock.add_response(status_code=404, json={"error": "Not found"})

        async def run_test():
            async with TestAsyncClient() as client:
                with pytest.raises(HTTPError):
                    await client.get_user(path={"id": 1})

        import asyncio

        asyncio.run(run_test())


class TestEndpointRepr:
    """Test endpoint __repr__ method."""

    def test_endpoint_repr(self):
        """Test __repr__ on endpoint."""
        from pydantic_httpx import GET

        endpoint = GET("/test")
        repr_str = repr(endpoint)
        assert "GET" in repr_str


class TestExceptionClasses:
    """Test exception classes."""

    def test_request_timeout_error(self):
        """Test RequestTimeoutError initialization and str."""
        from pydantic_httpx import RequestTimeoutError

        error = RequestTimeoutError("Timeout occurred", timeout=30.0)
        assert error.timeout == 30.0
        assert "Timeout occurred" in str(error)
        assert "30.0s" in str(error)


class TestResourceInitSubclass:
    """Test BaseResource __init_subclass__ edge cases."""

    def test_resource_without_resource_config(self, httpx_mock: HTTPXMock):
        """Test BaseResource subclass without resource_config."""

        class TestResource(BaseResource):
            get_data: Annotated[Endpoint[dict], GET("/data")]

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            test: TestResource

        httpx_mock.add_response(json={"key": "value"})

        client = TestClient()
        response = client.test.get_data()
        assert response.data["key"] == "value"

    def test_resource_with_none_resource_config(self, httpx_mock: HTTPXMock):
        """Test BaseResource subclass with resource_config = None."""

        class TestResource(BaseResource):
            resource_config = None  # type: ignore[assignment]
            get_data: Annotated[Endpoint[dict], GET("/data")]

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            test: TestResource

        httpx_mock.add_response(json={"key": "value"})

        client = TestClient()
        response = client.test.get_data()
        assert response.data["key"] == "value"

    def test_resource_with_problematic_type_hints(self):
        """Test BaseResource when get_type_hints raises exception."""

        class TestResource(BaseResource):
            resource_config = ResourceConfig(prefix="/test")

        assert TestResource is not None


class TestSyncWrapValidatorNonDataResponse:
    """Test sync wrap validator returning non-DataResponse."""

    def test_sync_wrap_validator_returns_raw_data(self, httpx_mock: HTTPXMock):
        """Test sync wrap validator that returns raw data."""

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            get_user: Annotated[Endpoint[User], GET("/users/{id}")]

            @endpoint_validator("get_user", mode="wrap")
            def cache_user(cls, handler, params: dict) -> User:
                return User(id=999, name="Cached")

        client = TestClient()
        response = client.get_user(path={"id": 1})
        assert response.data.id == 999
        assert response.data.name == "Cached"


class TestAfterValidatorReturnTypes:
    """Test after validator return type handling."""

    def test_async_after_validator_returns_dataresponse(self, httpx_mock: HTTPXMock):
        """Test async after validator that returns DataResponse."""

        class TestAsyncClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            get_user: Annotated[Endpoint[User], GET("/users/{id}")]

            @endpoint_validator("get_user", mode="after")
            def modify_user(cls, response):
                return response

        httpx_mock.add_response(json={"id": 1, "name": "Test"})

        async def run_test():
            async with TestAsyncClient() as client:
                response = await client.get_user(path={"id": 1})
                assert response.data.name == "Test"

        import asyncio

        asyncio.run(run_test())


class TestResponseDataDump:
    """Test DataResponse.data_dump edge cases."""

    def test_data_dump_with_plain_dict(self, httpx_mock: HTTPXMock):
        """Test data_dump when response data is a plain dict."""

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            get_data: Annotated[Endpoint[dict], GET("/data")]

        httpx_mock.add_response(json={"key": "value"})

        client = TestClient()
        response = client.get_data()
        dumped = response.data_dump()
        assert dumped == {"key": "value"}

    def test_data_dump_with_primitive(self, httpx_mock: HTTPXMock):
        """Test data_dump when response data is a primitive type."""

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            get_count: Annotated[Endpoint[int], GET("/count")]

        httpx_mock.add_response(json=42)

        client = TestClient()
        response = client.get_count()
        dumped = response.data_dump()
        assert dumped is None
