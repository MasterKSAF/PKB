"""Test configuration — shared across all server tests.

Usage:
    # Default — local server
    python data/tests/test_e2e.py

    # External server
    set TEST_API_URL=http://195.70.195.203/api/v1 && python data/tests/test_e2e.py
"""
import os
from typing import Optional


def get_api_url() -> str:
    """Get the API base URL.

    Default: http://localhost:8080/api/v1
    Override with TEST_API_URL env var (e.g. http://195.70.195.203/api/v1).
    """
    return os.environ.get("TEST_API_URL", "http://localhost:8080/api/v1")


def is_local() -> bool:
    """Check if target server is local (localhost/127.0.0.1)."""
    url = get_api_url()
    return "localhost" in url or "127.0.0.1" in url


def get_direct_rag_url() -> Optional[str]:
    """Get direct rag-search URL (internal service, accessible only locally)."""
    if is_local():
        return "http://localhost:8091/api/v1/rag/search"
    return None
