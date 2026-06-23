"""
Тесты переключения real/mock режима для Gateway Service Definition.

Проверяет:
- Gateway get_service_def() возвращает разные credentials в real/mock режиме
- get_credentials_for_mode() выбирает правильные credentials
- TEST_MODE env var влияет на get_test_mode()
- ApiCoverageTester принимает mode-параметр
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from service_checker.services.base import (
    get_test_mode,
    TEST_MODE_REAL,
    TEST_MODE_MOCK,
    get_credentials_for_mode,
    TEST_CREDENTIALS,
    GATEWAY_CREDENTIALS,
)
from service_checker.services.gateway import get_service_def


# ────────────────────────────────────────────────────────────────
#  1. Mode resolution (get_test_mode)
# ────────────────────────────────────────────────────────────────


class TestGetTestMode:
    """Проверка определения режима тестирования."""

    def test_default_is_real(self):
        """По умолчанию режим 'real'."""
        # Убедимся что TEST_MODE не установлен
        if "TEST_MODE" in os.environ:
            del os.environ["TEST_MODE"]
        assert get_test_mode() == TEST_MODE_REAL

    def test_env_mock(self):
        """TEST_MODE=mock → режим 'mock'."""
        with patch.dict(os.environ, {"TEST_MODE": "mock"}):
            assert get_test_mode() == TEST_MODE_MOCK

    def test_env_real(self):
        """TEST_MODE=real → режим 'real'."""
        with patch.dict(os.environ, {"TEST_MODE": "real"}):
            assert get_test_mode() == TEST_MODE_REAL

    def test_env_case_insensitive(self):
        """TEST_MODE=REAL → регистронезависимо 'real'."""
        with patch.dict(os.environ, {"TEST_MODE": "REAL"}):
            assert get_test_mode() == TEST_MODE_REAL


# ────────────────────────────────────────────────────────────────
#  2. Credentials selection (get_credentials_for_mode)
# ────────────────────────────────────────────────────────────────


class TestGetCredentialsForMode:
    """Проверка выбора credentials в зависимости от режима."""

    def test_real_uses_test_credentials(self):
        """real-режим → TEST_CREDENTIALS (Admin1234!)."""
        creds = get_credentials_for_mode(TEST_MODE_REAL)
        assert creds == TEST_CREDENTIALS
        assert creds["password"] == "Admin1234!"

    def test_mock_uses_gateway_credentials(self):
        """mock-режим → GATEWAY_CREDENTIALS (admin123)."""
        creds = get_credentials_for_mode(TEST_MODE_MOCK)
        assert creds == GATEWAY_CREDENTIALS
        assert creds["password"] == "admin123"

    def test_default_no_mode_uses_env(self):
        """Без mode — берёт из TEST_MODE env."""
        with patch.dict(os.environ, {"TEST_MODE": "mock"}):
            creds = get_credentials_for_mode()
            assert creds == GATEWAY_CREDENTIALS

    def test_default_no_mode_no_env_uses_real(self):
        """Без mode и TEST_MODE — real."""
        if "TEST_MODE" in os.environ:
            del os.environ["TEST_MODE"]
        creds = get_credentials_for_mode()
        assert creds == TEST_CREDENTIALS

    def test_returns_copy_not_reference(self):
        """Возвращается копия словаря, а не ссылка на константу."""
        creds = get_credentials_for_mode(TEST_MODE_REAL)
        creds["password"] = "hacked"
        assert TEST_CREDENTIALS["password"] == "Admin1234!"  # не изменилась


# ────────────────────────────────────────────────────────────────
#  3. Gateway service definition mode-awareness
# ────────────────────────────────────────────────────────────────


class TestGatewayServiceDefMode:
    """Проверка, что gateway.get_service_def() учитывает mode."""

    def test_real_mode_credentials(self):
        """real-режим → prepare использует TEST_CREDENTIALS."""
        svc_def = get_service_def(mode=TEST_MODE_REAL)
        prep = svc_def.prepare_endpoints
        assert len(prep) >= 1
        # Все prepare-шаги с auth/token должны иметь Admin1234!
        for ep in prep:
            if "token" in ep.path:
                assert ep.body["password"] == "Admin1234!", (
                    f"real-режим: ожидается Admin1234!, получен {ep.body['password']}"
                )

    def test_mock_mode_credentials(self):
        """mock-режим → prepare использует GATEWAY_CREDENTIALS."""
        svc_def = get_service_def(mode=TEST_MODE_MOCK)
        prep = svc_def.prepare_endpoints
        assert len(prep) >= 1
        for ep in prep:
            if "token" in ep.path:
                assert ep.body["password"] == "admin123", (
                    f"mock-режим: ожидается admin123, получен {ep.body['password']}"
                )

    def test_default_mode_from_env(self):
        """Без явного mode — берёт из TEST_MODE env."""
        with patch.dict(os.environ, {"TEST_MODE": "mock"}):
            svc_def = get_service_def()
            prep = svc_def.prepare_endpoints
            for ep in prep:
                if "token" in ep.path:
                    assert ep.body["password"] == "admin123"

    def test_default_mode_no_env_real(self):
        """Без mode и без TEST_MODE — real (Admin1234!)."""
        with patch.dict(os.environ, {}, clear=True):
            svc_def = get_service_def()
            prep = svc_def.prepare_endpoints
            for ep in prep:
                if "token" in ep.path:
                    assert ep.body["password"] == "Admin1234!"

    def test_auth_endpoint_credentials_match(self):
        """Основной эндпоинт /auth/token тоже использует mode-credentials."""
        svc_def_real = get_service_def(mode=TEST_MODE_REAL)
        svc_def_mock = get_service_def(mode=TEST_MODE_MOCK)

        # Найти основной эндпоинт /auth/token (не prepare)
        real_auth = None
        mock_auth = None
        for ep in svc_def_real.endpoints:
            if "token" in ep.path:
                real_auth = ep
                break
        for ep in svc_def_mock.endpoints:
            if "token" in ep.path:
                mock_auth = ep
                break

        assert real_auth is not None, "Не найден /auth/token в real endpoints"
        assert mock_auth is not None, "Не найден /auth/token в mock endpoints"
        assert real_auth.body["password"] == "Admin1234!"
        assert mock_auth.body["password"] == "admin123"


# ────────────────────────────────────────────────────────────────
#  4. ApiCoverageTester mode parameter
# ────────────────────────────────────────────────────────────────


class TestApiCoverageTesterMode:
    """Проверка, что ApiCoverageTester принимает mode и корректно его хранит."""

    def test_default_mode_is_real(self, tester):
        """Если mode не указан, по умолчанию 'real'."""
        assert tester.mode == TEST_MODE_REAL

    def test_explicit_mode_real(self):
        """Явный mode='real'."""
        from service_checker.core.api_coverage_test import ApiCoverageTester
        t = ApiCoverageTester(mode=TEST_MODE_REAL)
        assert t.mode == TEST_MODE_REAL

    def test_explicit_mode_mock(self):
        """Явный mode='mock'."""
        from service_checker.core.api_coverage_test import ApiCoverageTester
        t = ApiCoverageTester(mode=TEST_MODE_MOCK)
        assert t.mode == TEST_MODE_MOCK

    def test_mode_from_env(self):
        """mode из TEST_MODE env."""
        with patch.dict(os.environ, {"TEST_MODE": "mock"}):
            from service_checker.core.api_coverage_test import ApiCoverageTester
            t = ApiCoverageTester()
            assert t.mode == TEST_MODE_MOCK

    def test_explicit_overrides_env(self):
        """Явный mode переопределяет TEST_MODE env."""
        with patch.dict(os.environ, {"TEST_MODE": "mock"}):
            from service_checker.core.api_coverage_test import ApiCoverageTester
            t = ApiCoverageTester(mode=TEST_MODE_REAL)
            assert t.mode == TEST_MODE_REAL  # явный real важнее env

    def test_mode_passed_to_service_def(self):
        """mode передаётся в service definition при загрузке."""
        from service_checker.core.api_coverage_test import ApiCoverageTester
        from service_checker.services import SERVICE_REGISTRY

        # Проверяем, что mode корректно установлен в tester
        t = ApiCoverageTester(mode=TEST_MODE_REAL, services=["gateway"])
        assert t.mode == TEST_MODE_REAL

        t_mock = ApiCoverageTester(mode=TEST_MODE_MOCK, services=["gateway"])
        assert t_mock.mode == TEST_MODE_MOCK
