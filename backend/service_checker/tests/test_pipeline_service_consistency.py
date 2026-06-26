"""
Тесты согласованности Pipeline ↔ Service Registry ↔ Config.

Гарантирует, что пайплайны используют ТОЛЬКО те сервисы, эндпоинты, порты,
методы и expected_status, которые определены в SERVICE_REGISTRY.

Если обновили документацию API, а pipelines/services забыли обновить —
эти тесты упадут первыми, до Docker-прогона.
"""

from __future__ import annotations

import re

import pytest

from core.config import PIPELINE_SERVICE_MAP, SERVICE_DEFS, SERVICE_DISPLAY_NAMES
from pipelines import PIPELINE_REGISTRY
from pipelines.base import PipelineContext, PipelineStep, StepStatus, PipelineRunner
from services import SERVICE_REGISTRY, MODE_PORTS


# Внешние сервисы (не в SERVICE_REGISTRY, но используются пайплайнами)
EXTERNAL_SERVICES = {"minio", "tei"}
ALL_KNOWN_SERVICES = set(SERVICE_REGISTRY.keys()) | EXTERNAL_SERVICES

# Валидные HTTP-коды, используемые в expected_status
VALID_HTTP_CODES = {
    200, 201, 202, 204, 301, 302, 307,
    400, 401, 403, 404, 409, 422, 423, 429,
    500, 503,
}


# ────────────────────────────────────────────────────────────────
#  1. Каждый pipeline использует только зарегистрированные сервисы
# ────────────────────────────────────────────────────────────────


class TestPipelineServicesExist:
    """Сервисы из pipeline.services зарегистрированы в SERVICE_REGISTRY
    или входят в список известных внешних сервисов."""

    @pytest.mark.parametrize("pipeline_name", sorted(PIPELINE_REGISTRY.keys()))
    def test_services_known(self, pipeline_name):
        pipeline_cls = PIPELINE_REGISTRY[pipeline_name]
        pipeline = pipeline_cls()

        for svc in pipeline.services:
            assert svc in ALL_KNOWN_SERVICES, (
                f"Pipeline '{pipeline_name}' использует сервис '{svc}', "
                f"который не зарегистрирован в SERVICE_REGISTRY "
                f"и не входит в список известных внешних сервисов {EXTERNAL_SERVICES}. "
                f"Доступные: {', '.join(sorted(ALL_KNOWN_SERVICES))}"
            )

    @pytest.mark.parametrize("pipeline_name", sorted(PIPELINE_REGISTRY.keys()))
    def test_services_have_ports(self, pipeline_name):
        """Все сервисы pipeline имеют порт в MODE_PORTS или известны."""
        pipeline_cls = PIPELINE_REGISTRY[pipeline_name]
        pipeline = pipeline_cls()

        for svc in pipeline.services:
            if svc in EXTERNAL_SERVICES:
                continue
            assert svc in MODE_PORTS, (
                f"Pipeline '{pipeline_name}' использует сервис '{svc}', "
                f"у которого нет порта в MODE_PORTS"
            )
            assert MODE_PORTS[svc] > 0, (
                f"Pipeline '{pipeline_name}': порт сервиса '{svc}' = {MODE_PORTS[svc]}"
            )


# ────────────────────────────────────────────────────────────────
#  2. Шаги pipeline используют корректные порты и методы
# ────────────────────────────────────────────────────────────────


class TestPipelineStepsValid:
    """Атрибуты шагов pipeline согласованы с SERVICE_REGISTRY."""

    @pytest.mark.parametrize("pipeline_name", sorted(PIPELINE_REGISTRY.keys()))
    def test_step_ports_match_services(self, pipeline_name):
        """Порты шагов соответствуют MODE_PORTS для их сервиса."""
        pipeline_cls = PIPELINE_REGISTRY[pipeline_name]
        pipeline = pipeline_cls()
        steps = pipeline.build_steps(PipelineContext())

        for step in steps:
            expected_port = MODE_PORTS.get(step.service)
            if expected_port:
                assert step.port == expected_port, (
                    f"Pipeline '{pipeline_name}', шаг '{step.name}': "
                    f"сервис '{step.service}' имеет порт {expected_port} в MODE_PORTS, "
                    f"но в шаге указан {step.port}"
                )

    @pytest.mark.parametrize("pipeline_name", sorted(PIPELINE_REGISTRY.keys()))
    def test_step_methods_valid(self, pipeline_name):
        """Методы шагов — только HTTP-методы."""
        valid_methods = {"GET", "POST", "PUT", "PATCH", "DELETE"}
        pipeline_cls = PIPELINE_REGISTRY[pipeline_name]
        pipeline = pipeline_cls()
        steps = pipeline.build_steps(PipelineContext())

        for step in steps:
            assert step.method in valid_methods, (
                f"Pipeline '{pipeline_name}', шаг '{step.name}': "
                f"неизвестный метод '{step.method}'"
            )

    @pytest.mark.parametrize("pipeline_name", sorted(PIPELINE_REGISTRY.keys()))
    def test_expected_status_valid_http(self, pipeline_name):
        """expected_status — валидные HTTP-коды."""
        pipeline_cls = PIPELINE_REGISTRY[pipeline_name]
        pipeline = pipeline_cls()
        steps = pipeline.build_steps(PipelineContext())

        for step in steps:
            if step.expected_status is None:
                continue
            statuses = (step.expected_status
                        if isinstance(step.expected_status, set)
                        else {step.expected_status})
            for s in statuses:
                assert s in VALID_HTTP_CODES, (
                    f"Pipeline '{pipeline_name}', шаг '{step.name}': "
                    f"неизвестный HTTP-код {s} в expected_status"
                )


# ────────────────────────────────────────────────────────────────
#  3. Контекстная целостность: extract_keys не теряются
# ────────────────────────────────────────────────────────────────


class TestPipelineContextChain:
    """Цепочка extract_keys между шагами согласована.

    Каждый шаг, использующий плейсхолдер {key} в path/body (кроме __INLINE__),
    должен иметь предыдущий шаг (или prepare), который извлекает этот key.
    """

    @staticmethod
    def _collect_placeholders(obj, keys: set):
        """Рекурсивно собрать {placeholder} из строк в dict/list."""
        if isinstance(obj, dict):
            for v in obj.values():
                TestPipelineContextChain._collect_placeholders(v, keys)
        elif isinstance(obj, list):
            for item in obj:
                TestPipelineContextChain._collect_placeholders(item, keys)
        elif isinstance(obj, str):
            for m in re.finditer(r"\{(\w+)\}", obj):
                if not m.group(1).startswith("__INLINE"):
                    keys.add(m.group(1))

    @pytest.mark.parametrize("pipeline_name", sorted(PIPELINE_REGISTRY.keys()))
    def test_context_keys_are_extracted(self, pipeline_name):
        """Каждый {key} в path/body извлекается шагом ранее или встроен в класс."""
        pipeline_cls = PIPELINE_REGISTRY[pipeline_name]
        pipeline = pipeline_cls()
        steps = pipeline.build_steps(PipelineContext())

        builtin = set()
        for attr_name in ("TEST_PDF_KEY", "TEST_TASK_ID", "TEST_INVALID_PDF_KEY"):
            val = getattr(pipeline, attr_name, None)
            if val is not None:
                builtin.add(attr_name.lower().replace("test_", "").replace("_key", "_key"))

        extracted = set()
        for i, step in enumerate(steps):
            placeholders = set()
            if step.path:
                for m in re.finditer(r"\{(\w+)\}", step.path):
                    if not m.group(1).startswith("__INLINE"):
                        placeholders.add(m.group(1))
            if step.body:
                self._collect_placeholders(step.body, placeholders)

            for ph in placeholders:
                if ph in ("access_token", "refresh_token", "token"):
                    continue
                assert ph in extracted or ph in builtin or any(
                    prev_step.extract_keys and ph in prev_step.extract_keys
                    for prev_step in steps[:i]
                ), (
                    f"Pipeline '{pipeline_name}', шаг {i+1} '{step.name}': "
                    f"плейсхолдер '{{{ph}}}' используется в path/body, "
                    f"но ни один предыдущий шаг не извлекает этот ключ "
                    f"(extract_keys до шага: {[s.extract_keys for s in steps[:i]]})"
                )

            # Ключи, устанавливаемые check-функциями (не через extract_keys)
            if step.check and hasattr(step.check, '__name__'):
                if pipeline_name in (
                    "orchestrator_draft_lifecycle",
                    "orchestrator_document_reprocess",
                    "orchestrator_document_versions",
                    "orchestrator_full_document_lifecycle",
                ):
                    extracted.add("approved_doc_id")
                    extracted.add("approved_version_id")

            if step.extract_keys:
                extracted.update(step.extract_keys)

    @pytest.mark.parametrize("pipeline_name", sorted(PIPELINE_REGISTRY.keys()))
    def test_auth_token_flow(self, pipeline_name):
        """needs_auth=True шаги следуют ПОСЛЕ auth-шага с extract_keys=[access_token]."""
        pipeline_cls = PIPELINE_REGISTRY[pipeline_name]
        pipeline = pipeline_cls()
        steps = pipeline.build_steps(PipelineContext())

        has_auth_step = False
        for step in steps:
            if step.extract_keys and "access_token" in step.extract_keys:
                has_auth_step = True
            if step.needs_auth and not has_auth_step:
                if step.extract_keys and "access_token" in step.extract_keys:
                    continue
                if step.service in ("auth", "gateway"):
                    continue
                pytest.fail(
                    f"Pipeline '{pipeline_name}', шаг '{step.name}' "
                    f"(service={step.service}) требует auth (needs_auth=True), "
                    f"но до него нет auth-шага, извлекающего access_token"
                )


# ────────────────────────────────────────────────────────────────
#  4. Pipeline не использует "мёртвый" код
# ────────────────────────────────────────────────────────────────


class TestPipelineNoDeadServiceRefs:
    """Шаги не ссылаются на сервисы, которых нет в pipeline.services."""

    @pytest.mark.parametrize("pipeline_name", sorted(PIPELINE_REGISTRY.keys()))
    def test_step_services_in_pipeline_services(self, pipeline_name):
        pipeline_cls = PIPELINE_REGISTRY[pipeline_name]
        pipeline = pipeline_cls()
        steps = pipeline.build_steps(PipelineContext())

        for step in steps:
            if step.service in ("auth", "minio", "tei"):
                continue
            if step.service not in pipeline.services:
                pytest.fail(
                    f"Pipeline '{pipeline_name}', шаг '{step.name}': "
                    f"сервис '{step.service}' не указан в pipeline.services "
                    f"({pipeline.services}). Либо добавьте сервис в services, "
                    f"либо исправьте service шага."
                )


# ────────────────────────────────────────────────────────────────
#  5. PIPELINE_SERVICE_MAP совпадает с pipeline.services
# ────────────────────────────────────────────────────────────────


class TestPipelineServiceMap:
    """PIPELINE_SERVICE_MAP из config.py == pipeline.services (отчёт не устарел)."""

    @pytest.mark.parametrize("pipeline_name", sorted(PIPELINE_REGISTRY.keys()))
    def test_map_matches_pipeline_services(self, pipeline_name):
        pipeline_cls = PIPELINE_REGISTRY[pipeline_name]
        pipeline = pipeline_cls()

        actual = set(pipeline.services)
        mapped = set(PIPELINE_SERVICE_MAP.get(pipeline_name, []))

        for svc in EXTERNAL_SERVICES:
            actual.discard(svc)
            mapped.discard(svc)

        actual.discard("auth")
        mapped.discard("auth")
        # Gateway — прокси, не отслеживается отдельно в отчёте
        actual.discard("gateway")
        mapped.discard("gateway")

        assert actual == mapped, (
            f"Pipeline '{pipeline_name}':\n"
            f"  pipeline.services = {sorted(actual)}\n"
            f"  PIPELINE_SERVICE_MAP = {sorted(mapped)}\n"
            f"  Разница: {sorted(actual ^ mapped)}"
        )


# ────────────────────────────────────────────────────────────────
#  6. Тройная согласованность портов
# ────────────────────────────────────────────────────────────────


class TestPortConsistency:
    """Порты MODE_PORTS == _get_service_port() == SERVICE_DEFS."""

    def test_get_service_port_matches_mode_ports(self):
        """_get_service_port (PipelineRunner) == MODE_PORTS (services)."""
        runner = PipelineRunner()
        for svc in MODE_PORTS:
            rp = runner._get_service_port(svc)
            assert rp == MODE_PORTS[svc], (
                f"Порт '{svc}': MODE_PORTS={MODE_PORTS[svc]}, "
                f"_get_service_port={rp}"
            )

        # minio/tei теперь тоже в MODE_PORTS — проверены выше

    def test_service_defs_ports_match(self):
        """SERVICE_DEFS порты == MODE_PORTS для пересекающихся ключей."""
        for svc, info in SERVICE_DEFS.items():
            if svc in MODE_PORTS:
                assert info["port"] == MODE_PORTS[svc], (
                    f"Порт '{svc}': MODE_PORTS={MODE_PORTS[svc]}, "
                    f"SERVICE_DEFS={info['port']}"
                )

    def test_all_mode_ports_have_display_names(self):
        """Каждый ключ MODE_PORTS имеет отображаемое имя."""
        for svc in MODE_PORTS:
            assert svc in SERVICE_DISPLAY_NAMES, (
                f"'{svc}' есть в MODE_PORTS, но нет в SERVICE_DISPLAY_NAMES"
            )


# ────────────────────────────────────────────────────────────────
#  7. SERVICE_REGISTRY vs SERVICE_DEFS
# ────────────────────────────────────────────────────────────────


class TestServiceRegistryConsistency:
    """SERVICE_REGISTRY (checker) vs SERVICE_DEFS (config)."""

    def test_service_defs_have_all_registry_keys(self):
        """Все ключи SERVICE_REGISTRY есть в SERVICE_DEFS (кроме внешних)."""
        for svc in SERVICE_REGISTRY:
            if svc in ("gateway", "tei"):
                continue  # gateway-mock, tei — без SERVICE_DEFS
            assert svc in SERVICE_DEFS, (
                f"'{svc}' есть в SERVICE_REGISTRY, но нет в SERVICE_DEFS"
            )



