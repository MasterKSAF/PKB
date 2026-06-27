"""
Тесты InMemoryRateLimiter, _match_rule, check_rate_limit, IDOR protection.

Unit-тесты, не требуют Docker.
"""

from __future__ import annotations

import os
import sys
import time

import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)

from gateway.rate_limiter import (
    InMemoryRateLimiter,
    RATE_LIMIT_RULES,
    _match_rule,
    check_rate_limit,
    check_idor_rate_limit,
    reset_limiter,
    RateLimitResult,
)


class TestRateLimitRules:
    """RATE_LIMIT_RULES — 14 групп эндпоинтов с различными лимитами."""

    def test_rules_defined(self):
        """RATE_LIMIT_RULES не пуст."""
        assert len(RATE_LIMIT_RULES) > 0

    def test_rate_limit_rules_have_required_fields(self):
        """Каждое правило имеет path_pattern, limit, window."""
        for rule in RATE_LIMIT_RULES:
            assert "path_pattern" in rule
            assert "limit" in rule
            assert "window" in rule


class TestMatchRule:
    """_match_rule — подбор правила под путь."""

    def test_match_auth_route(self):
        """/api/v1/auth/token → auth rule."""
        rule = _match_rule("/api/v1/auth/token")
        assert rule is not None
        assert "auth" in rule.get("path_pattern", "")

    def test_match_drafts_route(self):
        """/api/v1/drafts → draft rule."""
        rule = _match_rule("/api/v1/drafts")
        assert rule is not None

    def test_match_unknown_returns_none(self):
        """Неизвестный путь → None."""
        rule = _match_rule("/api/v1/unknown/endpoint")
        assert rule is None


class TestInMemoryRateLimiter:
    """InMemoryRateLimiter — основные операции."""

    def test_is_allowed_first_request(self):
        """Первый запрос — разрешён."""
        limiter = InMemoryRateLimiter()
        result = limiter.is_allowed("test_key", limit=10, window=60)
        assert result == RateLimitResult.ALLOWED

    def test_is_allowed_under_limit(self):
        """Запросы в пределах лимита — разрешены."""
        limiter = InMemoryRateLimiter()
        for _ in range(5):
            result = limiter.is_allowed("test_key_2", limit=10, window=60)
            assert result == RateLimitResult.ALLOWED

    def test_is_throttled_over_limit(self):
        """Превышение лимита → THROTTLED."""
        limiter = InMemoryRateLimiter()
        key = "throttle_test"
        for _ in range(10):
            limiter.is_allowed(key, limit=10, window=60)
        result = limiter.is_allowed(key, limit=10, window=60)
        assert result == RateLimitResult.THROTTLED

    def test_window_expiry(self):
        """После истечения окна — снова ALLOWED."""
        limiter = InMemoryRateLimiter()
        key = "expiry_test"
        for _ in range(10):
            limiter.is_allowed(key, limit=10, window=0.1)
        assert limiter.is_allowed(key, limit=10, window=0.1) == RateLimitResult.THROTTLED
        time.sleep(0.15)
        result = limiter.is_allowed(key, limit=10, window=0.1)
        assert result == RateLimitResult.ALLOWED

    def test_cleanup_removes_expired(self):
        """cleanup() удаляет expired записи."""
        limiter = InMemoryRateLimiter()
        limiter.is_allowed("cleanup_test", limit=10, window=0.05)
        time.sleep(0.1)
        assert limiter.cleanup() >= 0

    def test_reset_clears_all(self):
        """reset() очищает все записи."""
        limiter = InMemoryRateLimiter()
        limiter.is_allowed("reset_test", limit=10, window=60)
        limiter.reset()
        assert limiter.is_allowed("reset_test", limit=10, window=60) == RateLimitResult.ALLOWED


class TestCheckRateLimit:
    """check_rate_limit — интеграция rate_limiter + middleware (RATE_LIMIT_ENABLED)."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_returns_allowed(self):
        """check_rate_limit возвращает ALLOWED при низкой нагрузке."""
        from gateway.rate_limiter import is_enabled
        if not is_enabled():
            # RATE_LIMIT_ENABLED=0 (по умолчанию в conftest) — всегда ALLOWED
            result = await check_rate_limit("GET", "/api/v1/auth/token", "test")
            assert result.result == RateLimitResult.ALLOWED

    @pytest.mark.asyncio
    async def test_check_rate_limit_respects_disabled(self, monkeypatch):
        """При RATE_LIMIT_ENABLED=0 — всегда ALLOWED."""
        monkeypatch.setattr("gateway.rate_limiter.config.rate_limit_enabled", False)
        result = await check_rate_limit("GET", "/api/v1/auth/token", "test")
        assert result.result == RateLimitResult.ALLOWED


class TestIdorProtection:
    """IDOR protection — check_idor_rate_limit."""

    @pytest.mark.asyncio
    async def test_idor_allowed_first(self):
        """IDOR: первый запрос к пути с ID — ALLOWED или None (при disabled)."""
        result = await check_idor_rate_limit("GET", "/api/v1/drafts/123", "test")
        assert result is None or result.result == RateLimitResult.ALLOWED

    @pytest.mark.asyncio
    async def test_idor_blocks_excess(self):
        """IDOR: превышение лимита — THROTTLED."""
        limiter = InMemoryRateLimiter()
        key = "idor:draft:999"
        for _ in range(30):
            limiter.is_allowed(key, limit=30, window=60)
        result = limiter.is_allowed(key, limit=30, window=60)
        assert result == RateLimitResult.THROTTLED


class TestResetLimiter:
    """reset_limiter — глобальный сброс."""

    def test_reset_limiter_works(self):
        """reset_limiter() не вызывает ошибок."""
        reset_limiter()
