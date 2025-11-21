"""Integration tests for advanced HTTP features (query params, auth, cookies, etc.)."""

import httpx
from httpx import codes
from pydantic import BaseModel
from pytest_httpx import HTTPXMock

from pydantic_httpx import (
    GET,
    POST,
    Client,
    BaseResource,
    ClientConfig,
    ResponseEndpoint,
    ResourceConfig,
)


class User(BaseModel):
    """Test model for User."""

    id: int
    name: str
    email: str


class SearchParams(BaseModel):
    """Test model for query parameters."""

    status: str
    limit: int = 10


class UserResource(BaseResource):
    """Resource for testing Phase 2 features."""

    resource_config = ResourceConfig(prefix="/users")

    # Basic endpoints
    get: ResponseEndpoint[User] = GET("/{id}")
    create: ResponseEndpoint[User] = POST("")

    # Endpoint with query model
    search: ResponseEndpoint[list[User]] = GET("/search", query_model=SearchParams)

    # Endpoint with custom headers
    get_with_headers: ResponseEndpoint[User] = GET(
        "/{id}", headers={"X-Custom-Header": "test-value"}
    )

    # Endpoint with cookies
    get_with_cookies: ResponseEndpoint[User] = GET(
        "/{id}", cookies={"session_id": "abc123"}
    )

    # Endpoint with auth (Basic auth tuple)
    get_with_auth: ResponseEndpoint[User] = GET("/{id}", auth=("username", "password"))

    # Endpoint with custom timeout
    get_with_timeout: ResponseEndpoint[User] = GET("/{id}", timeout=30.0)

    # Endpoint with follow_redirects=False
    get_no_redirects: ResponseEndpoint[User] = GET("/{id}", follow_redirects=False)


class APIClient(Client):
    """Test client for Phase 2 features."""

    client_config = ClientConfig(base_url="https://api.example.com")

    users: UserResource


class TestQueryParameters:
    """Tests for query parameter handling."""

    def test_query_parameters_without_model(self, httpx_mock: HTTPXMock) -> None:
        """Test that query parameters are sent correctly without validation."""
        # We'll test with the search endpoint which doesn't require the model
        httpx_mock.add_response(
            url="https://api.example.com/users/search?status=active&limit=5",
            method="GET",
            json=[
                {"id": 1, "name": "John", "email": "john@example.com"},
            ],
        )

        client = APIClient()
        # Using search endpoint and passing query params as kwargs
        # (bypassing validation)
        response = client.users.search(status="active", limit=5)

        assert len(response.data) == 1
        # Verify the request was made with correct query params
        request = httpx_mock.get_request()
        assert request is not None
        assert "status=active" in str(request.url)
        assert "limit=5" in str(request.url)

    def test_query_parameters_with_model(self, httpx_mock: HTTPXMock) -> None:
        """Test that query parameters are validated when model provided."""
        httpx_mock.add_response(
            url="https://api.example.com/users/search?status=active&limit=10",
            method="GET",
            json=[
                {"id": 1, "name": "John", "email": "john@example.com"},
                {"id": 2, "name": "Jane", "email": "jane@example.com"},
            ],
        )

        client = APIClient()
        response = client.users.search(status="active", limit=10)

        assert len(response.data) == 2
        # Verify the request was made
        request = httpx_mock.get_request()
        assert request is not None
        assert "status=active" in str(request.url)


class TestCustomHeaders:
    """Tests for custom header handling."""

    def test_endpoint_custom_headers(self, httpx_mock: HTTPXMock) -> None:
        """Test that endpoint-specific headers are sent."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="GET",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )

        client = APIClient()
        response = client.users.get_with_headers(id=1)

        assert response.data.name == "John"
        # Verify the custom header was sent
        request = httpx_mock.get_request()
        assert request is not None
        assert request.headers["X-Custom-Header"] == "test-value"

    def test_client_and_endpoint_headers_merge(self, httpx_mock: HTTPXMock) -> None:
        """Test that client and endpoint headers are merged."""

        class ClientWithHeaders(Client):
            client_config = ClientConfig(
                base_url="https://api.example.com",
                headers={"X-Client-Header": "client-value"},
            )
            users: UserResource

        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="GET",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )

        client = ClientWithHeaders()
        response = client.users.get_with_headers(id=1)

        assert response.data.name == "John"
        # Verify both headers were sent
        request = httpx_mock.get_request()
        assert request is not None
        assert request.headers["X-Client-Header"] == "client-value"
        assert request.headers["X-Custom-Header"] == "test-value"


class TestCookies:
    """Tests for cookie handling."""

    def test_endpoint_cookies(self, httpx_mock: HTTPXMock) -> None:
        """Test that endpoint-specific cookies are sent."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="GET",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )

        client = APIClient()
        response = client.users.get_with_cookies(id=1)

        assert response.data.name == "John"
        # Verify the cookie was sent
        request = httpx_mock.get_request()
        assert request is not None
        assert "session_id" in request.headers.get("cookie", "")


class TestAuthentication:
    """Tests for authentication handling."""

    def test_basic_auth_tuple(self, httpx_mock: HTTPXMock) -> None:
        """Test that Basic authentication with tuple is sent."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="GET",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )

        client = APIClient()
        response = client.users.get_with_auth(id=1)

        assert response.data.name == "John"
        # Verify auth header was sent
        request = httpx_mock.get_request()
        assert request is not None
        assert "authorization" in request.headers

    def test_custom_auth_class(self, httpx_mock: HTTPXMock) -> None:
        """Test that custom httpx.Auth class works."""

        class CustomAuth(httpx.Auth):
            def auth_flow(self, request):
                request.headers["X-Custom-Auth"] = "custom-value"
                yield request

        class CustomAuthResource(BaseResource):
            resource_config = ResourceConfig(prefix="/users")
            get: ResponseEndpoint[User] = GET("/{id}", auth=CustomAuth())

        class CustomAuthClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            users: CustomAuthResource

        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="GET",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )

        client = CustomAuthClient()
        response = client.users.get(id=1)

        assert response.data.name == "John"
        # Verify custom auth header was added
        request = httpx_mock.get_request()
        assert request is not None
        assert request.headers["X-Custom-Auth"] == "custom-value"


class TestTimeout:
    """Tests for custom timeout handling."""

    def test_endpoint_timeout_override(self, httpx_mock: HTTPXMock) -> None:
        """Test that endpoint timeout overrides client default."""
        httpx_mock.add_response(
            url="https://api.example.com/users/1",
            method="GET",
            json={"id": 1, "name": "John", "email": "john@example.com"},
        )

        client = APIClient()
        response = client.users.get_with_timeout(id=1)

        assert response.data.name == "John"
        # The timeout is passed to httpx, but we can't easily verify it was used
        # without actually timing out. The important thing is no error occurs.


class TestRedirects:
    """Tests for redirect handling."""

    def test_follow_redirects_false(self, httpx_mock: HTTPXMock) -> None:
        """Test that follow_redirects=False prevents following redirects."""

        # Create an endpoint that returns dict so we don't need to validate
        class RedirectResource(BaseResource):
            resource_config = ResourceConfig(prefix="/api")
            get: ResponseEndpoint[dict] = GET("/resource", follow_redirects=False)

        class RedirectClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            api: RedirectResource

        # Mock a redirect response
        httpx_mock.add_response(
            url="https://api.example.com/api/resource",
            method="GET",
            status_code=codes.MOVED_PERMANENTLY,
            headers={"Location": "https://api.example.com/api/new-resource"},
            json={"message": "redirecting"},
        )

        client = RedirectClient()
        response = client.api.get()

        # Should get the redirect response status (not follow it)
        assert response.status_code == codes.MOVED_PERMANENTLY
        # Verify the redirect header is present
        assert "location" in response.headers
        assert response.data["message"] == "redirecting"


class TestURLEncoding:
    """Tests for URL encoding with special characters."""

    def test_path_param_with_spaces(self, httpx_mock: HTTPXMock) -> None:
        """Test that path parameters with spaces are handled."""

        class ArticleResource(BaseResource):
            resource_config = ResourceConfig(prefix="/articles")
            get: ResponseEndpoint[dict] = GET("/{title}")

        class ArticleClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            articles: ArticleResource

        # HTTPX will URL-encode the path parameter
        httpx_mock.add_response(
            url="https://api.example.com/articles/hello%20world",
            method="GET",
            json={"title": "hello world", "content": "test"},
        )

        client = ArticleClient()
        response = client.articles.get(title="hello world")

        assert response.data["title"] == "hello world"

    def test_path_param_with_special_chars(self, httpx_mock: HTTPXMock) -> None:
        """Test that path parameters with special characters are handled."""

        class SearchResource(BaseResource):
            resource_config = ResourceConfig(prefix="/search")
            get: ResponseEndpoint[dict] = GET("/{query}")

        class SearchClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            search: SearchResource

        # Test with special characters that need encoding
        query = "foo@bar.com"
        httpx_mock.add_response(
            url="https://api.example.com/search/foo%40bar.com",
            method="GET",
            json={"query": query, "results": []},
        )

        client = SearchClient()
        response = client.search.get(query=query)

        assert response.data["query"] == query
