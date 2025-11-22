"""Tests for config TypedDicts."""

from pydantic_httpx import ClientConfig, ResourceConfig


class TestClientConfig:
    """Tests for ClientConfig TypedDict."""

    def test_default_values(self) -> None:
        """Test that empty ClientConfig dict works."""
        # ClientConfig is a TypedDict, so just use a plain dict
        config: ClientConfig = {}

        # Defaults are applied in Client.__init_subclass__
        # Here we just test that the TypedDict accepts valid fields
        assert config.get("base_url") is None
        assert config.get("timeout") is None

    def test_custom_values(self) -> None:
        """Test setting custom values in ClientConfig dict."""
        config: ClientConfig = {
            "base_url": "https://api.example.com",
            "timeout": 60.0,
            "headers": {"Authorization": "Bearer token"},
            "params": {"api_key": "secret"},
            "follow_redirects": False,
            "verify": False,
            "http2": True,
        }

        assert config["base_url"] == "https://api.example.com"
        assert config["timeout"] == 60.0
        assert config["headers"] == {"Authorization": "Bearer token"}
        assert config["params"] == {"api_key": "secret"}
        assert config["follow_redirects"] is False
        assert config["verify"] is False
        assert config["http2"] is True

    def test_immutable_dict_defaults(self) -> None:
        """Test that dict instances are independent."""
        config1: ClientConfig = {"headers": {}}
        config2: ClientConfig = {"headers": {}}

        config1["headers"]["X-Custom"] = "value"

        assert "X-Custom" in config1["headers"]
        assert "X-Custom" not in config2["headers"]


class TestResourceConfig:
    """Tests for ResourceConfig TypedDict."""

    def test_default_values(self) -> None:
        """Test that empty ResourceConfig dict works."""
        # ResourceConfig is a TypedDict, so just use a plain dict
        config: ResourceConfig = {}

        # Defaults are applied in BaseResource.__init_subclass__
        # Here we just test that the TypedDict accepts valid fields
        assert config.get("prefix") is None
        assert config.get("timeout") is None

    def test_custom_values(self) -> None:
        """Test setting custom values in ResourceConfig dict."""
        config: ResourceConfig = {
            "prefix": "/users",
            "timeout": 45.0,
            "headers": {"X-Resource": "users"},
            "validate_response": False,
            "raise_on_error": False,
            "description": "User management operations",
            "tags": ["users", "auth"],
        }

        assert config["prefix"] == "/users"
        assert config["timeout"] == 45.0
        assert config["headers"] == {"X-Resource": "users"}
        assert config["validate_response"] is False
        assert config["raise_on_error"] is False
        assert config["description"] == "User management operations"
        assert config["tags"] == ["users", "auth"]

    def test_prefix_validation_missing_leading_slash(self) -> None:
        """Test that prefix without leading slash - no runtime validation."""
        # TypedDict provides type hints only, no runtime validation
        # Validation would need to be added at usage time if desired
        config: ResourceConfig = {"prefix": "users"}
        assert config["prefix"] == "users"

    def test_prefix_validation_trailing_slash(self) -> None:
        """Test that prefix with trailing slash - no runtime validation."""
        # TypedDict provides type hints only, no runtime validation
        config: ResourceConfig = {"prefix": "/users/"}
        assert config["prefix"] == "/users/"

    def test_valid_prefix(self) -> None:
        """Test that valid prefix is accepted."""
        config: ResourceConfig = {"prefix": "/users"}
        assert config["prefix"] == "/users"

        config2: ResourceConfig = {"prefix": "/api/v1/users"}
        assert config2["prefix"] == "/api/v1/users"

    def test_empty_prefix_is_valid(self) -> None:
        """Test that empty prefix is valid."""
        config: ResourceConfig = {"prefix": ""}
        assert config["prefix"] == ""

    def test_immutable_dict_defaults(self) -> None:
        """Test that dict instances are independent."""
        config1: ResourceConfig = {"headers": {}, "tags": []}
        config2: ResourceConfig = {"headers": {}, "tags": []}

        config1["headers"]["X-Custom"] = "value"
        config1["tags"].append("test")

        assert "X-Custom" in config1["headers"]
        assert "X-Custom" not in config2["headers"]
        assert "test" in config1["tags"]
        assert "test" not in config2["tags"]
