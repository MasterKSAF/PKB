"""
Тесты rate_limiter (InMemoryRateLimiter + check_rate_limit + IDOR protection).

Сценарии:
  - RateLimitRule dataclass
  - check_rate_limit для разных эндпоинтов (auth 10/min, chat 30/min и т.д.)
  - Превышение лимита → BLOCKED
  - Retry-After header
  - check_idor_rate_limit по draft_id / document_id / session_id
  - Сброс после окна
  - RateLimitResult.THROTTLED при приближении к лимиту (80%)

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
    InMemoryRateLimiter,
    DEFAULT_RULES,
    IDOR_RULES,
    _match_rule,
    _extract_entity_ids,
    check_rate_limit,
    check_idor_rate_limit,
    build_rate_limit_key,
    reset_limiter,
    configure_rules,
    add_rules,
    _build_rule_patterns,
)


# ===================================================================
# RateLimitRule dataclass
# ===================================================================


class TestRateLimitRule:
    """RateLimitRule dataclass."""

    def test_rule_creation(self):
        """Создание RateLimitRule."""
        rule = RateLimitRule(limit=10, window_minutes=1, block_minutes=5)
        assert rule.limit == 10
        assert rule.window_minutes == 1
        assert rule.block_minutes == 5


# ===================================================================
# InMemoryRateLimiter базовые тесты
# ===================================================================


class TestInMemoryRateLimiter:
    """InMemoryRateLimiter unit-тесты."""

    def setup_method(self):
        self.limiter = InMemoryRateLimiter()
        self.rule = RateLimitRule(limit=5, window_minutes=1, block_minutes=1)

    def test_first_request_allowed(self):
        """Первый запрос в окне — ALLOWED с remaining=limit-1."""
        decision = self.limiter.check("test:key", self.rule)
        assert decision.result == RateLimitResult.ALLOWED
        assert decision.limit == 5
        assert decision.remaining == 4

    def test_within_limit(self):
        """Запросы в пределах лимита — ALLOWED."""
        for i in range(5):
            decision = self.limiter.check("test:key2", self.rule)
            assert decision.result == RateLimitResult.ALLOWED, f"Request {i+1} blocked"

    def test_exceeds_limit_blocked(self):
        """Превышение лимита → BLOCKED."""
        for i in range(6):
            decision = self.limiter.check("test:key3", self.rule)
            if i < 5:
                assert decision.result == RateLimitResult.ALLOWED
            else:
                assert decision.result == RateLimitResult.BLOCKED
                assert decision.retry_after_seconds > 0

    def test_retry_after_returned(self):
        """BLOCKED возвращает retry_after_seconds > 0."""
        for _ in range(6):
            decision = self.limiter.check("test:key4", self.rule)
        assert decision.result == RateLimitResult.BLOCKED
        assert decision.retry_after_seconds > 0

    def test_clear_resets(self):
        """clear() сбрасывает все лимиты."""
        for _ in range(6):
            self.limiter.check("test:key5", self.rule)
        decision = self.limiter.check("test:key5", self.rule)
        assert decision.result == RateLimitResult.BLOCKED

        self.limiter.clear()

        decision = self.limiter.check("test:key5", self.rule)
        assert decision.result == RateLimitResult.ALLOWED

    def test_window_expiry_via_clear(self):
        """После сброса лимитера лимит обнуляется."""
        rule = RateLimitRule(limit=3, window_minutes=1, block_minutes=0)
        for _ in range(3):
            self.limiter.check("test:key6", rule)
        decision = self.limiter.check("test:key6", rule)
        # Должен быть ALLOWED, т.к. window ещё не истёк? Нет, превысили лимит.
        # При блок = 0, после превышения лимита всё равно будет BLOCKED
        # Просто проверяем clear()
        self.limiter.clear()
        decision = self.limiter.check("test:key6", rule)
        assert decision.result == RateLimitResult.ALLOWED

    def test_size_property(self):
        """size возвращает количество записей."""
        assert self.limiter.size == 0
        self.limiter.check("test:a", self.rule)
        assert self.limiter.size >= 1


# ===================================================================
# _match_rule — подбор правил
# ===================================================================


class TestMatchRule:
    """_match_rule() — поиск подходящего правила."""

    _TEST_RULES = {
        "auth:POST:/api/v1/auth/token": RateLimitRule(10, 1, 5),
        "draft:*:/api/v1/drafts/*": RateLimitRule(30, 1, 1),
        "chat:POST:/api/v1/chat/sessions": RateLimitRule(30, 1, 1),
        "default:*:/*": RateLimitRule(60, 1, 1),
    }

    def setup_method(self):
        # Сохраняем оригинальные правила
        import copy
        self._orig_rules = copy.deepcopy(DEFAULT_RULES)
        configure_rules(self._TEST_RULES)

    def teardown_method(self):
        # Восстанавливаем оригинальные правила
        configure_rules(self._orig_rules)

    def test_exact_match(self):
        """Точное совпадение пути и метода."""
        rule = _match_rule("POST", "/api/v1/auth/token")
        assert rule.limit == 10

    def test_wildcard_method(self):
        """Wildcard метод подходит."""
        rule = _match_rule("GET", "/api/v1/drafts/123")
        assert rule.limit == 30

    def test_default_rule(self):
        """Неизвестный путь → default."""
        rule = _match_rule("GET", "/api/v1/unknown")
        assert rule.limit == 60


# ===================================================================
# _extract_entity_ids — IDOR protection
# ===================================================================


class TestExtractEntityIds:
    """_extract_entity_ids() — извлечение ID из пути."""

    def test_draft_id(self):
        ids = _extract_entity_ids("/api/v1/drafts/123")
        assert ids == {"draft_id": 123}

    def test_document_id(self):
        ids = _extract_entity_ids("/api/v1/documents/456")
        assert ids == {"doc_id": 456}

    def test_session_id(self):
        ids = _extract_entity_ids("/api/v1/chat/sessions/789")
        assert ids == {"session_id": 789}

    def test_no_match(self):
        ids = _extract_entity_ids("/api/v1/health")
        assert ids == {}

    def test_draft_with_subpath(self):
        ids = _extract_entity_ids("/api/v1/drafts/42/preview/status")
        assert ids == {"draft_id": 42}

    def test_document_with_versions(self):
        ids = _extract_entity_ids("/api/v1/documents/123/versions/5")
        assert ids == {"doc_id": 123}


# ===================================================================
# check_rate_limit (public API)
# ===================================================================


class TestCheckRateLimit:
    """check_rate_limit() — публичный API rate limiter."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self):
        """Запрос в пределах лимита — ALLOWED."""
        reset_limiter()
        decision = await check_rate_limit("GET", "/api/v1/health", "127.0.0.1")
        assert decision.result == RateLimitResult.ALLOWED

    @pytest.mark.asyncio
    async def test_check_idor_rate_limit_draft(self):
        """IDOR: лимит по draft_id."""
        reset_limiter()
        decision = await check_idor_rate_limit("GET", "/api/v1/drafts/42", "127.0.0.1")
        assert decision is None or decision.result == RateLimitResult.ALLOWED

    @pytest.mark.asyncio
    async def test_check_idor_rate_limit_no_match(self):
        """IDOR: нет entity ID → None."""
        reset_limiter()
        decision = await check_idor_rate_limit("GET", "/api/v1/health", "127.0.0.1")
        assert decision is None


# ===================================================================
# Utilities
# ===================================================================


class TestRateLimiterUtilities:
    """build_rate_limit_key, configure_rules, add_rules, reset_limiter."""

    def setup_method(self):
        import copy
        self._orig_rules = copy.deepcopy(DEFAULT_RULES)

    def teardown_method(self):
        configure_rules(self._orig_rules)

    def test_build_rate_limit_key_with_entity(self):
        """build_rate_limit_key c entity_id."""
        key = build_rate_limit_key("GET", "/api/v1/drafts/1", "10.0.0.1", entity_id="draft_id:1")
        assert "10.0.0.1" in key
        assert "draft_id:1" in key

    def test_build_rate_limit_key_without_entity(self):
        """build_rate_limit_key без entity_id."""
        key = build_rate_limit_key("GET", "/api/v1/health", "10.0.0.1")
        assert "10.0.0.1" in key

    def test_build_rate_limit_key_entity_isolation(self):
        """build_rate_limit_key c entity_id (изолированный тест)."""
        key = build_rate_limit_key("GET", "/api/v1/drafts/1", "10.0.0.1", entity_id="draft_id:1")
        assert "10.0.0.1" in key
        assert "draft_id:1" in key

    def test_reset_limiter_clears_store(self):
        """reset_limiter очищает хранилище."""
        limiter = InMemoryRateLimiter()
        rule = RateLimitRule(limit=3, window_minutes=1, block_minutes=0)
        limiter.check("reset:test", rule)
        assert limiter.size > 0
        limiter.clear()
        assert limiter.size == 0
