"""Configuration classes for clients and resources."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ClientConfig:
    """
    Configuration for BaseClient.

    Similar to Pydantic's model_config, this class defines settings
    for HTTP client behavior.

    Attributes:
        base_url: Base URL for all requests. Can be overridden per request.
        timeout: Default timeout in seconds for all requests.
        headers: Default headers to include in all requests.
        params: Default query parameters to include in all requests.
        follow_redirects: Whether to follow HTTP redirects.
        max_redirects: Maximum number of redirects to follow.
        verify: Whether to verify SSL certificates.
        cert: Client certificate for mutual TLS (path or tuple of cert + key).
        http2: Whether to enable HTTP/2 support.
        proxies: Proxy configuration dict (protocol -> URL).
        raise_on_error: Whether to raise HTTPError on 4xx/5xx status codes.
        validate_response: Whether to validate responses against Pydantic models.
    """

    base_url: str = ""
    timeout: float = 30.0
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    follow_redirects: bool = True
    max_redirects: int = 20
    verify: bool = True
    cert: str | tuple[str, str] | None = None
    http2: bool = False
    proxies: dict[str, str] = field(default_factory=dict)
    raise_on_error: bool = True
    validate_response: bool = True


@dataclass
class ResourceConfig:
    """
    Configuration for BaseResource.

    Similar to Pydantic's model_config, this class defines settings
    for a resource and its endpoints.

    Attributes:
        prefix: URL path prefix for all endpoints in this resource.
                Will be prepended to all endpoint paths.
        timeout: Timeout override for this resource. If None, uses client timeout.
        headers: Additional headers for all endpoints in this resource.
        validate_response: Whether to validate responses. If None, uses client setting.
        raise_on_error: Whether to raise on errors. If None, uses client setting.
        description: Human-readable description of this resource.
        tags: Tags for categorizing this resource (useful for documentation).
    """

    prefix: str = ""
    timeout: float | None = None
    headers: dict[str, str] = field(default_factory=dict)
    validate_response: bool | None = None
    raise_on_error: bool | None = None
    description: str | None = None
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.prefix:
            if not self.prefix.startswith("/"):
                raise ValueError(f"Resource prefix must start with '/': {self.prefix}")
            if self.prefix.endswith("/"):
                raise ValueError(
                    f"Resource prefix must not end with '/': {self.prefix}"
                )
