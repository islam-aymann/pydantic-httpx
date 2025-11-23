"""Test request body parameter handling (json, data, files, content)."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel
from pytest_httpx import HTTPXMock

from pydantic_httpx import POST, Client, ClientConfig, ResponseEndpoint


class LoginRequest(BaseModel):
    """Login request model for testing."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model for testing."""

    token: str
    user_id: int


class UploadResponse(BaseModel):
    """Upload response model for testing."""

    file_id: str
    filename: str


class TestJSONParameter:
    """Test JSON body parameter (existing functionality)."""

    def test_json_without_validation(self, httpx_mock: HTTPXMock) -> None:
        """Test json parameter without request model validation."""

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            create: Annotated[ResponseEndpoint[LoginResponse], POST("/create")]

        httpx_mock.add_response(
            url="https://api.example.com/create",
            method="POST",
            json={"token": "abc123", "user_id": 42},
        )

        client = TestClient()
        response = client.create(json={"username": "test", "password": "secret"})

        assert response.token == "abc123"
        assert response.user_id == 42

        # Verify httpx received json parameter
        request = httpx_mock.get_request()
        assert request.content == b'{"username":"test","password":"secret"}'

    def test_json_with_validation(self, httpx_mock: HTTPXMock) -> None:
        """Test json parameter with request model validation."""

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            create: Annotated[
                ResponseEndpoint[LoginResponse, LoginRequest], POST("/create")
            ]

        httpx_mock.add_response(
            url="https://api.example.com/create",
            method="POST",
            json={"token": "abc123", "user_id": 42},
        )

        client = TestClient()
        response = client.create(json={"username": "test", "password": "secret"})

        assert response.token == "abc123"
        assert response.user_id == 42

        # Verify request was validated and sent
        request = httpx_mock.get_request()
        assert request.content == b'{"username":"test","password":"secret"}'


class TestDataParameter:
    """Test form-encoded data parameter (NEW functionality)."""

    def test_data_without_validation(self, httpx_mock: HTTPXMock) -> None:
        """Test data parameter without request model validation."""

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            login: Annotated[ResponseEndpoint[LoginResponse], POST("/login")]

        httpx_mock.add_response(
            url="https://api.example.com/login",
            method="POST",
            json={"token": "form123", "user_id": 99},
        )

        client = TestClient()
        response = client.login(data={"username": "admin", "password": "pass"})

        assert response.token == "form123"
        assert response.user_id == 99

        # Verify httpx received data as form-encoded
        request = httpx_mock.get_request()
        assert b"username=admin" in request.content
        assert b"password=pass" in request.content
        assert request.headers["content-type"] == "application/x-www-form-urlencoded"

    def test_data_with_validation(self, httpx_mock: HTTPXMock) -> None:
        """Test data parameter with request model validation."""

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            login: Annotated[
                ResponseEndpoint[LoginResponse, LoginRequest], POST("/login")
            ]

        httpx_mock.add_response(
            url="https://api.example.com/login",
            method="POST",
            json={"token": "validated123", "user_id": 555},
        )

        client = TestClient()
        response = client.login(data={"username": "validated", "password": "secret"})

        assert response.token == "validated123"
        assert response.user_id == 555

        # Verify request was validated and sent as form
        request = httpx_mock.get_request()
        assert b"username=validated" in request.content
        assert request.headers["content-type"] == "application/x-www-form-urlencoded"


class TestFilesParameter:
    """Test files parameter (pass-through to httpx)."""

    def test_files_passthrough(self, httpx_mock: HTTPXMock) -> None:
        """Test files parameter is passed directly to httpx."""

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            upload: Annotated[ResponseEndpoint[UploadResponse], POST("/upload")]

        httpx_mock.add_response(
            url="https://api.example.com/upload",
            method="POST",
            json={"file_id": "file123", "filename": "test.txt"},
        )

        client = TestClient()

        # Simulate file upload (using bytes instead of actual file)
        file_content = b"Hello, World!"
        response = client.upload(files={"file": ("test.txt", file_content)})

        assert response.file_id == "file123"
        assert response.filename == "test.txt"

        # Verify httpx received files parameter
        request = httpx_mock.get_request()
        assert b"multipart/form-data" in request.headers["content-type"].encode()
        assert b"Hello, World!" in request.content

    def test_files_with_data_fields(self, httpx_mock: HTTPXMock) -> None:
        """Test files with additional data fields (multipart)."""

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            upload: Annotated[ResponseEndpoint[UploadResponse], POST("/upload")]

        httpx_mock.add_response(
            url="https://api.example.com/upload",
            method="POST",
            json={"file_id": "multi123", "filename": "document.pdf"},
        )

        client = TestClient()

        # Upload with both file and form fields
        file_content = b"PDF content here"
        response = client.upload(
            files={"document": ("document.pdf", file_content)},
            data={"description": "Important document", "category": "legal"},
        )

        assert response.file_id == "multi123"

        # Verify multipart request
        request = httpx_mock.get_request()
        assert b"multipart/form-data" in request.headers["content-type"].encode()
        assert b"PDF content here" in request.content
        assert b"description" in request.content
        assert b"Important document" in request.content


class TestContentParameter:
    """Test content parameter (raw binary, pass-through to httpx)."""

    def test_content_passthrough(self, httpx_mock: HTTPXMock) -> None:
        """Test content parameter is passed directly to httpx."""

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            webhook: Annotated[ResponseEndpoint[dict], POST("/webhook")]

        httpx_mock.add_response(
            url="https://api.example.com/webhook",
            method="POST",
            json={"status": "received", "bytes": 13},
        )

        client = TestClient()

        # Send raw binary content
        raw_data = b"Binary payload"
        response = client.webhook(content=raw_data)

        assert response.data["status"] == "received"
        assert response.data["bytes"] == 13

        # Verify httpx received raw content
        request = httpx_mock.get_request()
        assert request.content == b"Binary payload"


class TestBodyParameterExclusion:
    """Test that body parameters don't become query parameters."""

    def test_json_not_in_query_string(self, httpx_mock: HTTPXMock) -> None:
        """Test json parameter doesn't appear in query string."""

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            create: Annotated[ResponseEndpoint[LoginResponse], POST("/create")]

        httpx_mock.add_response(
            url="https://api.example.com/create",
            method="POST",
            json={"token": "test", "user_id": 1},
        )

        client = TestClient()
        client.create(json={"username": "test", "password": "pass"})

        request = httpx_mock.get_request()
        # URL should NOT contain json as query param
        assert "json=" not in str(request.url)
        assert "username=" not in str(request.url)

    def test_data_not_in_query_string(self, httpx_mock: HTTPXMock) -> None:
        """Test data parameter doesn't appear in query string."""

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            login: Annotated[ResponseEndpoint[LoginResponse], POST("/login")]

        httpx_mock.add_response(
            url="https://api.example.com/login",
            method="POST",
            json={"token": "test", "user_id": 1},
        )

        client = TestClient()
        client.login(data={"username": "test", "password": "pass"})

        request = httpx_mock.get_request()
        # URL should NOT contain data as query param
        assert "data=" not in str(request.url)
        assert "?username=" not in str(request.url)  # Should be in body, not URL

    def test_body_and_query_params_separated(self, httpx_mock: HTTPXMock) -> None:
        """Test body params and query params are properly separated."""

        class TestClient(Client):
            client_config = ClientConfig(base_url="https://api.example.com")
            search: Annotated[ResponseEndpoint[LoginResponse], POST("/search")]

        httpx_mock.add_response(
            url="https://api.example.com/search?page=1&limit=10",
            method="POST",
            json={"token": "test", "user_id": 1},
        )

        client = TestClient()
        client.search(
            json={"query": "test"},  # Body parameter
            page=1,  # Query parameter
            limit=10,  # Query parameter
        )

        request = httpx_mock.get_request()
        # Query params in URL
        assert "page=1" in str(request.url)
        assert "limit=10" in str(request.url)
        # JSON in body
        assert b'"query":"test"' in request.content
        # Body param NOT in URL
        assert "json=" not in str(request.url)


class TestAsyncClientBodyParams:
    """Test body parameters work with AsyncClient."""

    async def test_async_json_parameter(self, httpx_mock: HTTPXMock) -> None:
        """Test json parameter with AsyncClient."""
        from pydantic_httpx import AsyncClient

        class TestClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            create: Annotated[
                ResponseEndpoint[LoginResponse, LoginRequest], POST("/create")
            ]

        httpx_mock.add_response(
            url="https://api.example.com/create",
            method="POST",
            json={"token": "async123", "user_id": 42},
        )

        async with TestClient() as client:
            response = await client.create(
                json={"username": "async", "password": "test"}
            )

        assert response.token == "async123"
        assert response.user_id == 42

    async def test_async_data_parameter(self, httpx_mock: HTTPXMock) -> None:
        """Test data parameter with AsyncClient."""
        from pydantic_httpx import AsyncClient

        class TestClient(AsyncClient):
            client_config = ClientConfig(base_url="https://api.example.com")
            login: Annotated[
                ResponseEndpoint[LoginResponse, LoginRequest], POST("/login")
            ]

        httpx_mock.add_response(
            url="https://api.example.com/login",
            method="POST",
            json={"token": "form_async", "user_id": 99},
        )

        async with TestClient() as client:
            response = await client.login(
                data={"username": "async", "password": "form"}
            )

        assert response.token == "form_async"
        assert response.user_id == 99

        # Verify form encoding
        request = httpx_mock.get_request()
        assert request.headers["content-type"] == "application/x-www-form-urlencoded"
