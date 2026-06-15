import sys
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

# Добавляем backend в sys.path, чтобы работал импорт
# from service_checker.api_coverage_test import ...
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from service_checker.core.api_coverage_test import ApiCoverageTester
from service_checker.services.base import EndpointDef
from service_checker.services import MODE_PORTS


@pytest.fixture
def tester():
    """Создать экземпляр ApiCoverageTester с замокированным клиентом."""
    t = ApiCoverageTester()
    t.services_with_impl = set()
    t.client = MagicMock(spec=httpx.AsyncClient)
    # Добавляем тестовый сервис в MODE_PORTS чтобы избежать "Неизвестный порт"
    MODE_PORTS["test"] = 8080
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
