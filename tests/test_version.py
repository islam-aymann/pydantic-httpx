"""Test basic package functionality."""

import pydantic_httpx


def test_version() -> None:
    """Test that version is defined."""
    assert pydantic_httpx.__version__ == "0.2.1"
