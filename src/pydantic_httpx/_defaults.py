"""Default configuration values for clients and resources.

This module centralizes all default values to follow DRY principle
and make configuration management easier.
"""

from __future__ import annotations

from pydantic_httpx.config import ClientConfig, ResourceConfig

CLIENT_CONFIG_DEFAULTS: ClientConfig = {
    "base_url": "",
    "timeout": 30.0,
    "headers": {},
    "params": {},
    "follow_redirects": True,
    "max_redirects": 20,
    "verify": True,
    "cert": None,
    "http2": False,
    "proxies": {},
    "raise_on_error": True,
    "validate_response": True,
    "auth": None,
}

RESOURCE_CONFIG_DEFAULTS: ResourceConfig = {
    "prefix": "",
    "timeout": None,
    "headers": {},
    "validate_response": None,
    "raise_on_error": None,
    "description": None,
    "tags": [],
}
