import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

# Добавляем backend в sys.path, чтобы работал импорт
# from service_checker.api_coverage_test import ...
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from service_checker.core.api_coverage_test import ApiCoverageTester
from service_checker.services.base import (
    EndpointDef,
    get_test_mode,
    TEST_MODE_REAL,
    TEST_MODE_MOCK,
    get_credentials_for_mode,
    TEST_CREDENTIALS,
    GATEWAY_CREDENTIALS,
)
from service_checker.services import MODE_PORTS


@pytest.fixture
def mode() -> str:
    """Вернуть текущий режим тестирования (real/mock).

    Берётся из переменной окружения TEST_MODE, по умолчанию "real".
    """
    return get_test_mode()


@pytest.fixture
def tester(request):
    """Создать экземпляр ApiCoverageTester с замокированным клиентом.

    Используется для unit-тестов логики (без Docker).
    Для real-режима используйте `real_tester` фикстуру.
    """
    t = ApiCoverageTester()
    t.services_with_impl = set()
    t.client = MagicMock(spec=httpx.AsyncClient)
    # Добавляем тестовый сервис в MODE_PORTS чтобы избежать "Неизвестный порт"
    MODE_PORTS["test"] = 18080
    return t


@pytest.fixture
def real_tester(mode: str):
    """Создать экземпляр ApiCoverageTester для real-режима (без мока).

    Тестирует реальные Docker-сервисы.
    """
    t = ApiCoverageTester(mode=mode)
    # Для real-режима не мокаем клиент — используем реальный HTTP
    return t


@pytest.fixture
def make_endpoint():
    """Вспомогательная фабрика для создания EndpointDef."""
    def _make(path: str, group: str, method: str = "GET") -> EndpointDef:
        return EndpointDef(
            method=method,
            path=path,
            group=group,
            description=f"Test {group} endpoint",
        )
    return _make


def pytest_addoption(parser):
    """Добавить кастомные опции командной строки pytest."""
    parser.addoption(
        "--test-mode",
        action="store",
        default=None,
        choices=[TEST_MODE_REAL, TEST_MODE_MOCK],
        help=f"Режим тестирования: {TEST_MODE_REAL} или {TEST_MODE_MOCK}. "
             f"По умолчанию из TEST_MODE env или '{TEST_MODE_REAL}'.",
    )


def pytest_configure(config):
    """Настроить режим тестирования из опций командной строки."""
    # Если передан --test-mode, устанавливаем TEST_MODE env
    test_mode = config.getoption("--test-mode", default=None)
    if test_mode:
        os.environ["TEST_MODE"] = test_mode
