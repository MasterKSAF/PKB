"""Тесты пайплайна admin_user_lifecycle."""
from __future__ import annotations

from pipelines.base import PipelineContext
from pipelines.admin_user_lifecycle import AdminUserLifecyclePipeline


class TestAdminUserLifecyclePipeline:
    """Пайплайн admin_user_lifecycle — 16 шагов (+6 brute-force AU-3)."""

    def test_pipeline_attributes(self):
        p = AdminUserLifecyclePipeline()
        assert p.name == "admin_user_lifecycle"
        assert p.description
        assert "gateway" in p.services
        assert len(p.services) == 1

    def test_build_steps_count(self):
        p = AdminUserLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 16, f"Ожидалось 16 шагов, получено {len(steps)}"

    def test_build_steps_order(self):
        p = AdminUserLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация admin (через Gateway)",
            "Создание пользователя (через Gateway)",
            "Список пользователей (через Gateway)",
            "Аутентификация нового пользователя (через Gateway)",
            "Создание чат-сессии (новый пользователь, через Gateway)",
            "Отправка сообщения (новый пользователь, через Gateway)",
            "Получение истории чата (через Gateway)",
            # Brute-force (AU-3): 5 попыток
            "Брутфорс попытка 1/5 (через Gateway)",
            "Брутфорс попытка 2/5 (через Gateway)",
            "Брутфорс попытка 3/5 (через Gateway)",
            "Брутфорс попытка 4/5 (через Gateway)",
            "Брутфорс попытка 5/5 (через Gateway)",
            "Проверка блокировки после 5 неудач (через Gateway)",
            "Журнал аудита (через Gateway)",
            "Деактивация пользователя (через Gateway)",
            "Проверка 401 после деактивации (через Gateway)",
        ]
        actual = [s.name for s in steps]
        assert actual == expected_names, f"Порядок шагов:\n{actual}"

    def test_auth_steps_first(self):
        p = AdminUserLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        assert steps[0].service == "gateway"

    def test_last_step_expected_401(self):
        p = AdminUserLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        last = steps[-1]
        assert last.expected_status == {401, 403}

    def test_needs_auth_for_admin_operations(self):
        """Проверка, что admin-операции требуют auth, а логин — нет."""
        p = AdminUserLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        # Steps 0 (admin auth), 3 (new user auth), 7-12 (brute-force), 15 (401) не требуют auth
        # Brute-force шаги (7-12) не требуют auth — они проверяют защиту
        non_auth_indices = {0, 3, 7, 8, 9, 10, 11, 12, 15}
        auth_requiring = [s for i, s in enumerate(steps) if i not in non_auth_indices]
        for step in auth_requiring:
            assert step.needs_auth, f"Шаг '{step.name}' должен требовать auth"

    def test_no_skip_if(self):
        """Ни один шаг не имеет skip_if — пайплайн линейный."""
        p = AdminUserLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        for step in steps:
            assert step.skip_if is None, f"Шаг '{step.name}' не должен иметь skip_if"
