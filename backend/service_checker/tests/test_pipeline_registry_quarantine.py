"""Тесты пайплайна registry_quarantine."""
from __future__ import annotations

from pipelines.base import PipelineContext
from pipelines.registry_quarantine import RegistryQuarantinePipeline


class TestRegistryQuarantinePipeline:
    """Пайплайн registry_quarantine — 10 шагов."""

    def test_pipeline_attributes(self):
        p = RegistryQuarantinePipeline()
        assert p.name == "registry_quarantine"
        assert p.description
        assert "gateway" in p.services
        assert len(p.services) == 2

    def test_build_steps_count(self):
        p = RegistryQuarantinePipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 10, f"Ожидалось 10 шагов, получено {len(steps)}"

    def test_build_steps_order(self):
        p = RegistryQuarantinePipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация (через Gateway)",
            "Создать классификатор (через Gateway)",
            "Создать документ с неизвестным кодом (через Gateway)",
            "Список карантина (pending, через Gateway)",
            "Принять из карантина (accept, через Gateway)",
            "Валидация классификации (accept, через Gateway)",
            "Создать второй документ с неизвестным кодом (через Gateway)",
            "Список карантина (второй pending, через Gateway)",
            "Отклонить из карантина (reject, через Gateway)",
            "Валидация классификации (reject, через Gateway)",
        ]
        actual = [s.name for s in steps]
        assert actual == expected_names, f"Порядок шагов:\n{actual}"

    def test_accept_and_reject_both_present(self):
        p = RegistryQuarantinePipeline()
        steps = p.build_steps(PipelineContext())
        names = [s.name for s in steps]
        assert any("accept" in n.lower() for n in names)
        assert any("reject" in n.lower() for n in names)

    def test_all_steps_need_auth_except_first(self):
        p = RegistryQuarantinePipeline()
        steps = p.build_steps(PipelineContext())
        for step in steps[1:]:
            assert step.needs_auth, f"Шаг '{step.name}' должен требовать auth"

    def test_no_422_workaround(self):
        """Ни один шаг не использует 422 как обход — пайплайн только registry."""
        p = RegistryQuarantinePipeline()
        steps = p.build_steps(PipelineContext())
        for step in steps:
            if isinstance(step.expected_status, set):
                assert 422 not in step.expected_status, (
                    f"Шаг '{step.name}' не должен содержать 422 как обход"
                )
