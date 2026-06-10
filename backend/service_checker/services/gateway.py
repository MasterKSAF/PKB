"""
PKB Neuroassistant — Gateway Service API Definitions.

Gateway агрегирует API сервисов: auth + orchestrator + query + registry.
"""

from __future__ import annotations

from .base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
)
from .auth import get_service_def as get_auth_def
from .orchestrator import get_service_def as get_orchestrator_def
from .query import get_service_def as get_query_def
from .registry import get_service_def as get_registry_def

SERVICE_KEY = "gateway"
PORT = 8081
DISPLAY_NAME = "Gateway Service"


def get_service_def() -> ServiceDef:
    """Вернуть полное описание Gateway Service.

    Gateway включает в себя эндпоинты auth + orchestrator + query + registry.
    """
    auth_def = get_auth_def()
    orch_def = get_orchestrator_def()
    query_def = get_query_def()
    reg_def = get_registry_def()

    # Собираем все эндпоинты
    all_endpoints: list[EndpointDef] = [
        # Health
        EndpointDef("GET", f"{API_PREFIX}/system/health", "health",
            "Gateway health check",
            response_schema={"status": str, "version": str, "services": dict}),
    ]
    all_endpoints.extend(auth_def.endpoints)
    all_endpoints.extend(orch_def.endpoints)
    all_endpoints.extend(query_def.endpoints)
    all_endpoints.extend(reg_def.endpoints)

    # Prepare-эндпоинты (наследуем от подчинённых сервисов)
    all_prepare: list[EndpointDef] = []
    all_prepare.extend(auth_def.prepare_endpoints)
    all_prepare.extend(orch_def.prepare_endpoints)
    all_prepare.extend(query_def.prepare_endpoints)
    all_prepare.extend(reg_def.prepare_endpoints)

    return ServiceDef(
        service_key=SERVICE_KEY,
        display_name=DISPLAY_NAME,
        port=PORT,
        needs_auth=False,  # токен получаем через prepare
        endpoints=all_endpoints,
        prepare_endpoints=all_prepare,
        depends_on=["auth", "orchestrator", "query", "registry"],
        base_data={},
    )
