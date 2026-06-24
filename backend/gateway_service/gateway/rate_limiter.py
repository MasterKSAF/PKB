"""
Rate limiter for Gateway Service (CM-2, CM-3, GW-4, GW-6).

Бэкенд — InMemory (достаточно для single-instance Gateway).

Лимиты настраиваются через переменные окружения:
  RATE_LIMIT_ENABLED=1
  RATE_LIMIT_DEFAULT=60,1   # лимит, окно_в_минутах
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class RateLimitRule:
    """Правило лимита для группы эндпоинтов."""

    limit: int            # макс. запросов в окне
    window_minutes: int   # окно в минутах
    block_minutes: int    # блокировка при превышении


class RateLimitResult(Enum):
    ALLOWED = "allowed"
    THROTTLED = "throttled"   # превышен лимит, но не заблокирован
    BLOCKED = "blocked"       # заблокирован


@dataclass
class RateLimitDecision:
    result: RateLimitResult
    retry_after_seconds: int = 0
    limit: int = 0
    remaining: int = 0
    reset_at: float = 0.0


# ---------------------------------------------------------------------------
# Default rules (из common_api.md — Rate Limiting)
# ---------------------------------------------------------------------------

DEFAULT_RULES: Dict[str, RateLimitRule] = {
    # Auth
    "auth:POST:/api/v1/auth/token":    RateLimitRule(10, 1, 5),
    "auth:POST:/api/v1/auth/refresh":  RateLimitRule(20, 1, 5),
    # Documents / Drafts
    "draft:POST:/api/v1/drafts":       RateLimitRule(10, 1, 1),
    "draft:*:/api/v1/drafts/*":        RateLimitRule(30, 1, 1),
    "doc:GET:/api/v1/documents":       RateLimitRule(100, 1, 1),
    "doc:*:/api/v1/documents/*":       RateLimitRule(60, 1, 1),
    # Chat
    "chat:POST:/api/v1/chat/sessions":     RateLimitRule(30, 1, 1),
    "chat:POST:/api/v1/chat/sessions/*/messages": RateLimitRule(30, 1, 1),
    "chat:*:/api/v1/chat/*":               RateLimitRule(60, 1, 1),
    # Text search
    "text:POST:/api/v1/text/search":   RateLimitRule(30, 1, 1),
    # Admin
    "admin:GET:/api/v1/admin/*":       RateLimitRule(60, 1, 1),
    "admin:POST:/api/v1/admin/*":      RateLimitRule(20, 1, 1),
    "admin:*:/api/v1/admin/*":         RateLimitRule(30, 1, 1),
    # Registry
    "registry:GET:/api/v1/registry/*": RateLimitRule(100, 1, 1),
    "registry:POST:/api/v1/registry/*": RateLimitRule(30, 1, 1),
    # Default
    "default:*:/*":                    RateLimitRule(60, 1, 1),
}

# Entity ID rate limits (IDOR protection — CM-3, GW-6)
# Ограничение запросов к конкретному draft_id / document_id / session_id
IDOR_RULES: Dict[str, RateLimitRule] = {
    "draft_id":  RateLimitRule(30, 1, 5),   # 30 запросов/мин к одному draft_id
    "doc_id":    RateLimitRule(30, 1, 5),   # 30 запросов/мин к одному document_id
    "session_id": RateLimitRule(30, 1, 5),  # 30 запросов/мин к одной session_id
}


# ---------------------------------------------------------------------------
# Pattern matching helpers
# ---------------------------------------------------------------------------

_RULE_CACHE: List[Tuple[re.Pattern, str, RateLimitRule]] = []


def _build_rule_patterns(rules: Dict[str, RateLimitRule]) -> None:
    """Превращает ключи правил в compiled regex."""
    _RULE_CACHE.clear()
    for key, rule in rules.items():
        parts = key.split(":", 2)
        if len(parts) != 3:
            continue
        method_pattern, path_pattern = parts[1], parts[2]
        # Превращаем wildcard в regex
        regex_str = "^" + re.escape(path_pattern).replace(r"\*", ".*") + "$"
        try:
            compiled = re.compile(regex_str, re.I)
            _RULE_CACHE.append((compiled, method_pattern, rule))
        except re.error:
            logger.warning("Invalid rate limit pattern: %s", key)


_build_rule_patterns(DEFAULT_RULES)


def _match_rule(method: str, path: str) -> RateLimitRule:
    """Ищет подходящее правило для запроса."""
    for pattern, method_pat, rule in _RULE_CACHE:
        if method_pat != "*" and method_pat.upper() != method.upper():
            continue
        if pattern.match(path):
            return rule
    return DEFAULT_RULES["default:*:/*"]


# ---------------------------------------------------------------------------
# Entity ID patterns (IDOR protection)
# ---------------------------------------------------------------------------

_IDOR_PATH_PATTERNS: Dict[str, re.Pattern] = {
    "draft_id": re.compile(r"/api/v1/drafts/(\d+)"),
    "doc_id": re.compile(r"/api/v1/documents/(\d+)"),
    "session_id": re.compile(r"/api/v1/chat/sessions/(\d+)"),
}


def _extract_entity_ids(path: str) -> Dict[str, int]:
    """Извлекает entity ID из пути."""
    result: Dict[str, int] = {}
    for key, pattern in _IDOR_PATH_PATTERNS.items():
        m = pattern.search(path)
        if m:
            result[key] = int(m.group(1))
    return result


# ---------------------------------------------------------------------------
# In-memory rate limiter (dev, mock, fallback)
# ---------------------------------------------------------------------------


class InMemoryRateLimiter:
    """Токен-бакетный rate limiter in-memory.

    Для каждого ключа (ip+rule или entity_id+rule) хранит:
      - bucket_window: начало окна (timestamp)
      - bucket_count:  количество запросов в окне
    """

    def __init__(self):
        self._store: Dict[str, dict] = {}
        self._cleanup_interval = 300  # 5 мин
        self._last_cleanup = time.time()

    def _cleanup(self, now: float) -> None:
        """Удаляет истёкшие записи."""
        if now - self._last_cleanup < self._cleanup_interval:
            return
        self._last_cleanup = now
        expired = [
            k for k, v in self._store.items()
            if now - v.get("window_start", 0) > v.get("window_seconds", 3600) * 2
        ]
        for k in expired:
            del self._store[k]

    def check(self, key: str, rule: RateLimitRule) -> RateLimitDecision:
        """Проверяет лимит для ключа."""
        now = time.time()
        self._cleanup(now)
        window_seconds = rule.window_minutes * 60
        entry = self._store.get(key)
        if entry is None:
            self._store[key] = {
                "window_start": now,
                "count": 1,
                "blocked_until": 0,
            }
            return RateLimitDecision(
                result=RateLimitResult.ALLOWED,
                limit=rule.limit,
                remaining=rule.limit - 1,
                reset_at=now + window_seconds,
            )

        # Проверка блокировки
        if entry.get("blocked_until", 0) > now:
            return RateLimitDecision(
                result=RateLimitResult.BLOCKED,
                retry_after_seconds=int(entry["blocked_until"] - now),
                limit=rule.limit,
                remaining=0,
                reset_at=entry["blocked_until"],
            )

        # Сброс окна
        if now - entry.get("window_start", 0) > window_seconds:
            entry["window_start"] = now
            entry["count"] = 1
            entry["blocked_until"] = 0
            return RateLimitDecision(
                result=RateLimitResult.ALLOWED,
                limit=rule.limit,
                remaining=rule.limit - 1,
                reset_at=now + window_seconds,
            )

        entry["count"] += 1
        if entry["count"] > rule.limit:
            # Блокируем
            entry["blocked_until"] = now + rule.block_minutes * 60
            return RateLimitDecision(
                result=RateLimitResult.BLOCKED,
                retry_after_seconds=rule.block_minutes * 60,
                limit=rule.limit,
                remaining=0,
                reset_at=entry["blocked_until"],
            )
        if entry["count"] >= rule.limit * 0.8:
            # Предупреждение (80% лимита)
            logger.warning(
                "Rate limit threshold 80%% reached: key=%s count=%d limit=%d",
                key[:64], entry["count"], rule.limit,
            )

        return RateLimitDecision(
            result=RateLimitResult.ALLOWED,
            limit=rule.limit,
            remaining=rule.limit - entry["count"],
            reset_at=entry["window_start"] + window_seconds,
        )

    def clear(self) -> None:
        """Сбрасывает все лимиты (для тестов)."""
        self._store.clear()

    @property
    def size(self) -> int:
        return len(self._store)


# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

_limiter = InMemoryRateLimiter()


def get_limiter() -> InMemoryRateLimiter:
    """Возвращает in-memory rate limiter."""
    return _limiter



def build_rate_limit_key(
    method: str,
    path: str,
    client_ip: str,
    entity_id: Optional[str] = None,
) -> str:
    """Формирует ключ для rate limiter."""
    if entity_id:
        return f"{client_ip}:entity:{entity_id}"
    rule = _match_rule(method, path)
    return f"{client_ip}:{method}:{path}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_RATE_LIMIT_ENABLED = None


def is_enabled() -> bool:
    """Проверяет, включён ли rate limiting."""
    global _RATE_LIMIT_ENABLED
    if _RATE_LIMIT_ENABLED is None:
        _RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "1").lower() in (
            "1", "true", "yes"
        )
    return _RATE_LIMIT_ENABLED


async def check_rate_limit(
    method: str,
    path: str,
    client_ip: str,
) -> RateLimitDecision:
    """Проверяет rate limit для запроса."""
    if not is_enabled():
        return RateLimitDecision(result=RateLimitResult.ALLOWED)

    limiter = get_limiter()
    rule = _match_rule(method, path)
    key = build_rate_limit_key(method, path, client_ip)
    return limiter.check(key, rule)


async def check_idor_rate_limit(
    method: str,
    path: str,
    client_ip: str,
) -> Optional[RateLimitDecision]:
    """IDOR protection: проверяет rate limit для entity ID (CM-3, GW-6).

    Если в пути найден draft_id / document_id / session_id —
    применяет дополнительный лимит к этому ID.
    """
    if not is_enabled():
        return None

    entity_ids = _extract_entity_ids(path)
    if not entity_ids:
        return None

    limiter = get_limiter()
    worst: Optional[RateLimitDecision] = None

    for entity_type, entity_val in entity_ids.items():
        idor_rule = IDOR_RULES.get(entity_type)
        if idor_rule is None:
            continue
        key = build_rate_limit_key(method, path, client_ip, entity_id=f"{entity_type}:{entity_val}")
        decision = limiter.check(key, idor_rule)
        if decision.result == RateLimitResult.BLOCKED:
            return decision
        if worst is None or decision.remaining < worst.remaining:
            worst = decision

    return worst


def reset_limiter() -> None:
    """Сбрасывает лимитер (для тестов)."""
    _limiter.clear()


def configure_rules(rules: Dict[str, RateLimitRule]) -> None:
    """Заменяет правила целиком (для тестов/переконфигурации)."""
    global DEFAULT_RULES
    DEFAULT_RULES = rules.copy()
    _build_rule_patterns(DEFAULT_RULES)


def add_rules(rules: Dict[str, RateLimitRule]) -> None:
    """Добавляет правила к существующим (не заменяет)."""
    global DEFAULT_RULES
    DEFAULT_RULES.update(rules)
    _build_rule_patterns(DEFAULT_RULES)
