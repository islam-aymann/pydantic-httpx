"""Tests for config classes."""

import pytest

from pydantic_httpx import ClientConfig, ResourceConfig


class TestClientConfig:
    """Tests for ClientConfig."""

    def test_default_values(self) -> None:
        """Test that ClientConfig has sensible defaults."""
        config = ClientConfig()

        assert config.base_url == ""
        assert config.timeout == 30.0
        assert config.headers == {}
        assert config.params == {}
        assert config.follow_redirects is True
        assert config.max_redirects == 20
        assert config.verify is True
        assert config.cert is None
        assert config.http2 is False
        assert config.proxies == {}
        assert config.raise_on_error is True
        assert config.validate_response is True

    def test_custom_values(self) -> None:
        """Test setting custom values."""
        config = ClientConfig(
            base_url="https://api.example.com",
            timeout=60.0,
            headers={"Authorization": "Bearer token"},
            params={"api_key": "secret"},
            follow_redirects=False,
            verify=False,
            http2=True,
        )

        assert config.base_url == "https://api.example.com"
        assert config.timeout == 60.0
        assert config.headers == {"Authorization": "Bearer token"}
        assert config.params == {"api_key": "secret"}
        assert config.follow_redirects is False
        assert config.verify is False
        assert config.http2 is True

    def test_immutable_dict_defaults(self) -> None:
        """Test that dict defaults are not shared between instances."""
        config1 = ClientConfig()
        config2 = ClientConfig()

        config1.headers["X-Custom"] = "value"

        assert "X-Custom" in config1.headers
        assert "X-Custom" not in config2.headers


class TestResourceConfig:
    """Tests for ResourceConfig."""

    def test_default_values(self) -> None:
        """Test that ResourceConfig has sensible defaults."""
        config = ResourceConfig()

        assert config.prefix == ""
        assert config.timeout is None
        assert config.headers == {}
        assert config.validate_response is None
        assert config.raise_on_error is None
        assert config.description is None
        assert config.tags == []

    def test_custom_values(self) -> None:
        """Test setting custom values."""
        config = ResourceConfig(
            prefix="/users",
            timeout=45.0,
            headers={"X-Resource": "users"},
            validate_response=False,
            raise_on_error=False,
            description="User management operations",
            tags=["users", "auth"],
        )

        assert config.prefix == "/users"
        assert config.timeout == 45.0
        assert config.headers == {"X-Resource": "users"}
        assert config.validate_response is False
        assert config.raise_on_error is False
        assert config.description == "User management operations"
        assert config.tags == ["users", "auth"]

    def test_prefix_validation_missing_leading_slash(self) -> None:
        """Test that prefix without leading slash raises ValueError."""
        with pytest.raises(ValueError, match="must start with '/'"):
            ResourceConfig(prefix="users")

    def test_prefix_validation_trailing_slash(self) -> None:
        """Test that prefix with trailing slash raises ValueError."""
        with pytest.raises(ValueError, match="must not end with '/'"):
            ResourceConfig(prefix="/users/")

    def test_valid_prefix(self) -> None:
        """Test that valid prefix is accepted."""
        config = ResourceConfig(prefix="/users")
        assert config.prefix == "/users"

        config2 = ResourceConfig(prefix="/api/v1/users")
        assert config2.prefix == "/api/v1/users"

    def test_empty_prefix_is_valid(self) -> None:
        """Test that empty prefix is valid."""
        config = ResourceConfig(prefix="")
        assert config.prefix == ""

    def test_immutable_dict_defaults(self) -> None:
        """Test that dict defaults are not shared between instances."""
        config1 = ResourceConfig()
        config2 = ResourceConfig()

        config1.headers["X-Custom"] = "value"
        config1.tags.append("test")

        assert "X-Custom" in config1.headers
        assert "X-Custom" not in config2.headers
        assert "test" in config1.tags
        assert "test" not in config2.tags
