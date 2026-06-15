"""Тесты пайплайна admin_user_lifecycle."""
from __future__ import annotations

from pipelines.base import PipelineContext
from pipelines.admin_user_lifecycle import AdminUserLifecyclePipeline


class TestAdminUserLifecyclePipeline:
    """Пайплайн admin_user_lifecycle — 10 шагов."""

    def test_pipeline_attributes(self):
        p = AdminUserLifecyclePipeline()
        assert p.name == "admin_user_lifecycle"
        assert p.description
        assert len(p.services) == 2

    def test_build_steps_count(self):
        p = AdminUserLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 10, f"Ожидалось 10 шагов, получено {len(steps)}"

    def test_build_steps_order(self):
        p = AdminUserLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация admin",
            "Создание пользователя",
            "Список пользователей",
            "Аутентификация нового пользователя",
            "Создание чат-сессии (новый пользователь)",
            "Отправка сообщения (новый пользователь)",
            "Получение истории чата",
            "Журнал аудита",
            "Деактивация пользователя",
            "Проверка 401 после деактивации",
        ]
        actual = [s.name for s in steps]
        assert actual == expected_names, f"Порядок шагов:\n{actual}"

    def test_auth_steps_first(self):
        p = AdminUserLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        assert steps[0].service == "auth"

    def test_last_step_expected_401(self):
        p = AdminUserLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        last = steps[-1]
        assert last.expected_status == {401, 403}

    def test_needs_auth_for_admin_operations(self):
        """Проверка, что admin-операции требуют auth, а логин — нет."""
        p = AdminUserLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        # Steps 0 (admin auth), 3 (new user auth), 9 (401 check) не требуют auth
        auth_requiring = [s for i, s in enumerate(steps) if i not in (0, 3, 9)]
        for step in auth_requiring:
            assert step.needs_auth, f"Шаг '{step.name}' должен требовать auth"

    def test_no_skip_if(self):
        """Ни один шаг не имеет skip_if — пайплайн линейный."""
        p = AdminUserLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        for step in steps:
            assert step.skip_if is None, f"Шаг '{step.name}' не должен иметь skip_if"
