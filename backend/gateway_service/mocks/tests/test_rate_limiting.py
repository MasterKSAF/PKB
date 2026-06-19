"""
Тесты rate limiting и IDOR protection (CM-2, CM-3, GW-4, GW-6).

Проверяет:
  1. Rate limit по группам эндпоинтов
  2. IDOR rate limit по draft_id / document_id / session_id
  3. Сброс лимитера между тестами
  4. Retry-After заголовок
  5. 429 ответ

Тесты используют отдельное минимальное FastAPI-приложение,
чтобы не влиять на глобальное состояние mock gateway.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from gateway.rate_limiter import (
    IDOR_RULES as MOD_IDOR_RULES,
    DEFAULT_RULES,
    RateLimitRule,
    RateLimitResult,
    _build_rule_patterns,
    reset_limiter,
    is_enabled,
    _match_rule,
    _extract_entity_ids,
    check_rate_limit,
    check_idor_rate_limit,
)


# ---------------------------------------------------------------------------
# Тестовое FastAPI-приложение с RateLimitMiddleware
# ---------------------------------------------------------------------------

class TestRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = "127.0.0.1"
        method = request.method
        path = request.url.path

        decision = await check_rate_limit(method, path, client_ip)
        if decision.result == RateLimitResult.BLOCKED:
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "TOO_MANY_REQUESTS", "message": "rate limit"}},
                headers={"Retry-After": str(decision.retry_after_seconds)},
            )

        idor_decision = await check_idor_rate_limit(method, path, client_ip)
        if idor_decision and idor_decision.result == RateLimitResult.BLOCKED:
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "TOO_MANY_REQUESTS", "message": "idor limit"}},
                headers={"Retry-After": str(idor_decision.retry_after_seconds)},
            )

        return await call_next(request)


_test_app = FastAPI()
_test_app.add_middleware(TestRateLimitMiddleware)


@_test_app.get("/api/v1/health")
async def health():
    return {"status": "ok"}


@_test_app.get("/api/v1/system/health")
async def system_health():
    return {"status": "ok"}


@_test_app.get("/api/v1/drafts/{draft_id}")
async def get_draft(draft_id: int):
    return {"draft_id": draft_id}


@_test_app.get("/api/v1/documents/{doc_id}")
async def get_document(doc_id: int):
    return {"doc_id": doc_id}


@_test_app.get("/api/v1/chat/sessions/{session_id}")
async def get_session(session_id: int):
    return {"session_id": session_id}


@_test_app.get("/api/v1/documents")
async def list_documents():
    return {"documents": []}


client = TestClient(_test_app)


# ---------------------------------------------------------------------------
# Test rules — низкие лимиты для быстрой проверки
# ---------------------------------------------------------------------------

_TEST_RULES = {
    "system:GET:/api/v1/system/health": RateLimitRule(3, 1, 1),   # 3 запроса/мин
    "health:GET:/api/v1/health":        RateLimitRule(50, 1, 1),  # высокий
    "draft:GET:/api/v1/drafts":         RateLimitRule(2, 1, 1),   # 2 запроса/мин
    "doc:GET:/api/v1/documents":        RateLimitRule(5, 1, 1),
    "chat:GET:/api/v1/chat":           RateLimitRule(2, 1, 1),
    "default:*:/*":                     RateLimitRule(50, 1, 1),
}

_TEST_IDOR = {
    "draft_id":  RateLimitRule(2, 1, 1),   # 2 запроса/мин к одному draft_id
    "doc_id":    RateLimitRule(2, 1, 1),
    "session_id": RateLimitRule(2, 1, 1),
}


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Сбрасывает rate limiter перед каждым тестом."""
    DEFAULT_RULES.clear()
    DEFAULT_RULES.update(_TEST_RULES)
    _build_rule_patterns(DEFAULT_RULES)
    MOD_IDOR_RULES.clear()
    MOD_IDOR_RULES.update(_TEST_IDOR)
    reset_limiter()
    yield


# ===================================================================
# Rate limit tests
# ===================================================================


def test_rate_limit_allowed():
    """Запрос в пределах лимита проходит."""
    resp = client.get("/api/v1/system/health")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


def test_rate_limit_blocked():
    """Превышение лимита → 429."""
    for i in range(5):
        resp = client.get("/api/v1/system/health")
        if i < 3:
            assert resp.status_code == 200, (
                f"Request {i+1} should be allowed, got {resp.status_code}"
            )
        else:
            assert resp.status_code == 429, (
                f"Request {i+1} should be blocked, got {resp.status_code}: {resp.text}"
            )
            data = resp.json()
            assert "error" in data
            assert data["error"]["code"] == "TOO_MANY_REQUESTS"
            assert "Retry-After" in resp.headers


def test_rate_limit_retry_after_header():
    """429 ответ содержит Retry-After заголовок."""
    for _ in range(5):
        resp = client.get("/api/v1/system/health")
        if resp.status_code == 429:
            assert "Retry-After" in resp.headers
            retry_after = int(resp.headers["Retry-After"])
            assert retry_after > 0
            return
    pytest.fail("Should have hit rate limit")


def test_rate_limit_different_endpoints_independent():
    """Разные эндпоинты имеют независимые лимиты."""
    for _ in range(5):
        client.get("/api/v1/system/health")

    resp = client.get("/api/v1/documents")
    assert resp.status_code == 200, (
        "Different endpoint should not be rate limited"
    )


def test_rate_limit_reset():
    """После сброса лимитера счётчик обнуляется."""
    for _ in range(5):
        client.get("/api/v1/system/health")

    resp = client.get("/api/v1/system/health")
    assert resp.status_code == 429

    reset_limiter()

    resp = client.get("/api/v1/system/health")
    assert resp.status_code == 200, "After reset should be allowed"


# ===================================================================
# IDOR protection tests (CM-3, GW-6)
# ===================================================================


def test_idor_draft_id_blocked():
    """IDOR: превышение лимита по draft_id → 429."""
    for i in range(5):
        resp = client.get("/api/v1/drafts/42")
        if i < 2:
            assert resp.status_code == 200, (
                f"Draft request {i+1} should be allowed, got {resp.status_code}"
            )
        else:
            assert resp.status_code == 429, (
                f"Draft request {i+1} should be blocked: {resp.text}"
            )
            data = resp.json()
            assert "error" in data
            assert data["error"]["code"] == "TOO_MANY_REQUESTS"


def test_idor_document_id_blocked():
    """IDOR: превышение лимита по document_id → 429."""
    for i in range(5):
        resp = client.get("/api/v1/documents/99")
        if i < 2:
            assert resp.status_code == 200
        else:
            assert resp.status_code == 429


def test_idor_session_id_blocked():
    """IDOR: превышение лимита по session_id → 429."""
    for i in range(5):
        resp = client.get("/api/v1/chat/sessions/7")
        if i < 2:
            assert resp.status_code == 200
        else:
            assert resp.status_code == 429


def test_idor_different_ids_independent():
    """IDOR: разные ID имеют независимые лимиты."""
    for _ in range(5):
        client.get("/api/v1/drafts/1")

    resp = client.get("/api/v1/drafts/2")
    assert resp.status_code == 200, (
        "Different draft_id should have independent limit"
    )


def test_idor_only_entity_paths():
    """IDOR: запросы без entity ID не проверяются IDOR-лимитом."""
    for _ in range(5):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200, (
            f"Health endpoint should not be IDOR-limited, got {resp.status_code}"
        )


def test_idor_reset_after_window():
    """IDOR: после сброса лимитер позволяет запросы."""
    for _ in range(5):
        client.get("/api/v1/drafts/42")

    resp = client.get("/api/v1/drafts/42")
    assert resp.status_code == 429

    reset_limiter()

    resp = client.get("/api/v1/drafts/42")
    assert resp.status_code == 200, "After reset IDOR should allow requests"


# ===================================================================
# Unit tests for rate_limiter module internals
# ===================================================================


class TestRateLimiterInternals:

    def test_match_rule_default(self):
        """Для неизвестного пути применяется default-правило."""
        rule = _match_rule("GET", "/api/v1/unknown/route")
        assert rule.limit == 50

    def test_match_rule_specific(self):
        """Для известного пути применяется специфичное правило."""
        rule = _match_rule("GET", "/api/v1/drafts")
        assert rule.limit == 2

    def test_match_rule_method_specific(self):
        """Правила учитывают HTTP-метод."""
        rule = _match_rule("GET", "/api/v1/system/health")
        assert rule.limit == 3

    def test_extract_entity_ids_draft(self):
        """Извлечение draft_id из пути."""
        ids = _extract_entity_ids("/api/v1/drafts/123")
        assert ids == {"draft_id": 123}

    def test_extract_entity_ids_document(self):
        """Извлечение document_id из пути."""
        ids = _extract_entity_ids("/api/v1/documents/456")
        assert ids == {"doc_id": 456}

    def test_extract_entity_ids_session(self):
        """Извлечение session_id из пути."""
        ids = _extract_entity_ids("/api/v1/chat/sessions/789")
        assert ids == {"session_id": 789}

    def test_extract_entity_ids_no_match(self):
        """Путь без entity ID → пустой словарь."""
        ids = _extract_entity_ids("/api/v1/health")
        assert ids == {}

    def test_extract_entity_ids_query_params(self):
        """Путь с query string без entity ID → пустой словарь."""
        ids = _extract_entity_ids("/api/v1/registry/search?q=test")
        assert ids == {}

    def test_is_enabled_default(self):
        """Rate limit включён по умолчанию."""
        assert is_enabled() is True


class TestIDORPatternsEdgeCases:

    def test_extract_draft_with_subpath(self):
        """Извлечение draft_id из вложенного пути."""
        ids = _extract_entity_ids("/api/v1/drafts/42/preview/status")
        assert ids == {"draft_id": 42}

    def test_extract_document_with_versions(self):
        """Извлечение document_id из пути с версиями."""
        ids = _extract_entity_ids("/api/v1/documents/123/versions/5")
        assert ids == {"doc_id": 123}
