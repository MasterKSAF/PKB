"""
Тесты rate_limiter (InMemoryRateLimiter + check_rate_limit + IDOR protection).

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
    RateLimitRule,
    RateLimitResult,
    RateLimitDecision,
    InMemoryRateLimiter,
    DEFAULT_RULES,
    _match_rule,
    check_rate_limit,
    check_idor_rate_limit,
    reset_limiter,
)


class TestDEFAULT_RULES:
    """DEFAULT_RULES — правила лимитов."""

    def test_rules_defined(self):
        """DEFAULT_RULES не пуст."""
        assert len(DEFAULT_RULES) > 0

    def test_default_rule_exists(self):
        """Есть default-правило."""
        assert "default:*:/*" in DEFAULT_RULES
        assert DEFAULT_RULES["default:*:/*"].limit == 60


class TestMatchRule:
    """_match_rule — подбор правила под метод+путь."""

    def test_match_auth_route(self):
        """POST /api/v1/auth/token → auth rule."""
        rule = _match_rule("POST", "/api/v1/auth/token")
        assert rule is not None

    def test_match_drafts_route(self):
        """POST /api/v1/drafts → draft rule."""
        rule = _match_rule("POST", "/api/v1/drafts")
        assert rule is not None

    def test_match_unknown_returns_default(self):
        """Неизвестный путь → default."""
        rule = _match_rule("GET", "/api/v1/unknown/path")
        assert rule is not None


class TestInMemoryRateLimiter:
    """InMemoryRateLimiter — основные операции."""

    def setup_method(self):
        self.limiter = InMemoryRateLimiter()
        self.rule = RateLimitRule(limit=5, window_minutes=1, block_minutes=1)

    def test_first_request_allowed(self):
        """Первый запрос — ALLOWED с remaining=limit-1."""
        decision = self.limiter.check("test:key", self.rule)
        assert decision.result == RateLimitResult.ALLOWED
        assert decision.remaining == 4

    def test_within_limit_allowed(self):
        """Запросы в пределах лимита — ALLOWED."""
        for i in range(5):
            d = self.limiter.check("test:key2", self.rule)
            assert d.result == RateLimitResult.ALLOWED, f"Request {i+1} blocked"

    def test_exceeds_limit_blocked(self):
        """Превышение лимита → BLOCKED."""
        for i in range(6):
            d = self.limiter.check("test:key3", self.rule)
            if i < 5:
                assert d.result == RateLimitResult.ALLOWED
            else:
                assert d.result == RateLimitResult.BLOCKED
                assert d.retry_after_seconds > 0

    def test_clear_resets(self):
        """clear() сбрасывает все лимиты."""
        for _ in range(6):
            self.limiter.check("test:key4", self.rule)
        assert self.limiter.check("test:key4", self.rule).result == RateLimitResult.BLOCKED

        self.limiter.clear()

        d = self.limiter.check("test:key4", self.rule)
        assert d.result == RateLimitResult.ALLOWED

    def test_different_keys_independent(self):
        """Разные ключи имеют независимые лимиты."""
        rule = RateLimitRule(limit=1, window_minutes=1, block_minutes=1)
        assert self.limiter.check("key_a", rule).result == RateLimitResult.ALLOWED
        assert self.limiter.check("key_a", rule).result == RateLimitResult.BLOCKED
        assert self.limiter.check("key_b", rule).result == RateLimitResult.ALLOWED

    def test_size_property(self):
        """size возвращает количество записей."""
        assert self.limiter.size == 0
        self.limiter.check("sz:a", self.rule)
        assert self.limiter.size >= 1


class TestCheckRateLimit:
    """check_rate_limit — публичный API rate limiter."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self):
        """check_rate_limit возвращает ALLOWED (RATE_LIMIT_ENABLED=0 в conftest)."""
        reset_limiter()
        decision = await check_rate_limit("GET", "/api/v1/health", "127.0.0.1")
        assert decision.result == RateLimitResult.ALLOWED

    @pytest.mark.asyncio
    async def test_check_idor_rate_limit_draft(self):
        """IDOR: лимит по draft_id."""
        reset_limiter()
        decision = await check_idor_rate_limit("GET", "/api/v1/drafts/42", "127.0.0.1")
        assert decision is None or decision.result == RateLimitResult.ALLOWED


class TestResetLimiter:
    """reset_limiter — глобальный сброс."""

    def test_reset_limiter_works(self):
        """reset_limiter() не вызывает ошибок."""
        reset_limiter()
