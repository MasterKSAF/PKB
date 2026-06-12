"""
Unit tests for the REAL gateway's resolve_service() function.

Tests service routing logic directly from gateway.client, covering:
  - All /api/v1/registry/ sub-paths resolve to "registry"
  - Old paths without /registry/ return None (404)
  - Other service prefixes (auth, orchestrator, query) still work
  - Edge cases: exact match, trailing slashes, unknown paths, health endpoint
"""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import pytest
from gateway.client import resolve_service


# ===========================================================================
# Registry paths — /api/v1/registry/
# ===========================================================================

class TestRegistryPaths:
    """All paths under /api/v1/registry/ must resolve to 'registry'."""

    @pytest.mark.parametrize("path", [
        "/api/v1/registry/classifiers",
        "/api/v1/registry/classifiers/",
        "/api/v1/registry/classifiers/tree",
        "/api/v1/registry/terminology",
        "/api/v1/registry/terminology/",
        "/api/v1/registry/documents",
        "/api/v1/registry/documents/",
        "/api/v1/registry/common/stats",
        "/api/v1/registry/drafts",
    ])
    def test_registry_paths(self, path: str):
        assert resolve_service(path) == "registry"


# ===========================================================================
# Old paths (no /registry/) — should return None
# ===========================================================================

class TestOldPathsReturnNone:
    """Legacy paths without /api/v1/registry/ prefix must return None."""

    @pytest.mark.parametrize("path", [
        "/api/v1/classifiers",
        "/api/v1/classifiers/",
        "/api/v1/terminology",
        "/api/v1/common/stats",
    ])
    def test_old_paths_return_none(self, path: str):
        assert resolve_service(path) is None


# ===========================================================================
# Other service routes
# ===========================================================================

class TestOtherServices:
    """Other service prefixes must still resolve correctly."""

    def test_auth_me(self):
        assert resolve_service("/api/v1/auth/me") == "auth"

    def test_documents(self):
        assert resolve_service("/api/v1/documents/") == "orchestrator"

    def test_chat_sessions(self):
        assert resolve_service("/api/v1/chat/sessions") == "query"


# ===========================================================================
# Edge cases
# ===========================================================================

class TestEdgeCases:
    """Boundary and edge cases for resolve_service."""

    def test_exact_match(self):
        """Exact match without trailing slash: /api/v1/registry → 'registry'."""
        assert resolve_service("/api/v1/registry") == "registry"

    def test_health_returns_none(self):
        """system/health is a gateway-owned endpoint, should return None."""
        assert resolve_service("/api/v1/system/health") is None

    def test_unknown_path_returns_none(self):
        """Completely unrecognised path should return None."""
        assert resolve_service("/api/v1/unknown/endpoint") is None


# ===========================================================================
# Trailing slash handling
# ===========================================================================

class TestTrailingSlashHandling:
    """resolve_service must not be affected by trailing slashes (no 307
    redirect needed — the function itself normalises the path)."""

    @pytest.mark.parametrize("path,expected", [
        ("/api/v1/registry/", "registry"),
        ("/api/v1/documents/", "orchestrator"),
        ("/api/v1/documents", "orchestrator"),
    ])
    def test_trailing_slashes(self, path: str, expected: str):
        """Both with and without trailing slash should resolve identically."""
        assert resolve_service(path) == expected
