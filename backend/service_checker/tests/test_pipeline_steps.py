"""Тесты определения шагов пайплайнов (существующие 3 пайплайна).

Новые пайплайны (full_document_lifecycle, admin_user_lifecycle,
registry_quarantine, orchestrator_draft_lifecycle, multi_document_cross_search)
— в отдельных файлах test_pipeline_*.py.
"""
from __future__ import annotations

import pytest

from pipelines.base import PipelineContext, StepStatus
from pipelines.document_processing import DocumentProcessingPipeline
from pipelines.chat_inference import ChatInferencePipeline
from pipelines.registry_lifecycle import RegistryLifecyclePipeline


class TestDocumentProcessingPipeline:
    """Пайплайн document_processing — 15 шагов (+preview, +validate/document)."""

    def test_pipeline_attributes(self):
        p = DocumentProcessingPipeline()
        assert p.name == "document_processing"
        assert p.description == "Полный цикл обработки документа"
        assert "auth" in p.services
        assert "minio" in p.services
        assert len(p.services) == 7

    def test_build_steps_count(self):
        p = DocumentProcessingPipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 15, (
            f"Ожидалось 15 шагов, получено {len(steps)}\n"
            f"Шаги: {[s.name for s in steps]}"
        )

    def test_build_steps_order(self):
        p = DocumentProcessingPipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация",
            "Создание bucket documents",
            "Загрузка PDF в MinIO",
            "Запуск парсинга",
            "Статус парсинга (longpoll)",
            "Результат парсинга",
            "Предпросмотр метаданных",
            "Валидация метаданных (бизнес-ключ)",
            "Проверка уникальности документа",
            "Конвертация JSON",
            "Валидация документа",
            "Сохранение документа в Registry",
            "Проверка preview_snapshot в документе",
            "Построение чанков и индексация",
            "Поиск по индексу RAG Search",
        ]
        actual_names = [s.name for s in steps]
        assert actual_names == expected_names, f"Порядок шагов не совпадает:\nОжидалось: {expected_names}\nПолучено: {actual_names}"

    def test_build_steps_services(self):
        p = DocumentProcessingPipeline()
        steps = p.build_steps(PipelineContext())
        services = [s.service for s in steps]
        assert "auth" in services  # вместо gateway
        assert "minio" in services

    def test_step_ports(self):
        p = DocumentProcessingPipeline()
        steps = p.build_steps(PipelineContext())
        for step in steps:
            assert step.port > 0, f"Шаг '{step.name}' имеет порт 0"
            assert step.method in ("GET", "POST", "PUT", "PATCH", "DELETE"), \
                f"Шаг '{step.name}' имеет неизвестный метод {step.method}"

    def test_step_expected_status(self):
        p = DocumentProcessingPipeline()
        steps = p.build_steps(PipelineContext())
        # Проверка статусов: шаги через gateway имеют те же ожидаемые статусы
        actual = [s.expected_status for s in steps]
        expected = [200, {200, 409}, 200, 202, 200, 200, 200, 200, {200}, 200, 200, {201, 409}, 200, {200, 201, 202}, 200]
        assert actual == expected, f"Ожидаемые статусы не совпадают:\n{actual}\n"

    def test_steps_initial_status(self):
        p = DocumentProcessingPipeline()
        steps = p.build_steps(PipelineContext())
        for step in steps:
            assert step.status == StepStatus.PENDING, \
                f"Шаг '{step.name}' должен иметь статус PENDING"


class TestChatInferencePipeline:
    """Пайплайн chat_inference — 6 шагов."""

    def test_pipeline_attributes(self):
        p = ChatInferencePipeline()
        assert p.name == "chat_inference"
        assert p.description == "Чат-сессия с поиском по проиндексированным документам"
        assert "gateway" in p.services
        assert len(p.services) == 2

    def test_build_steps_count(self):
        p = ChatInferencePipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 6, (
            f"Ожидалось 6 шагов, получено {len(steps)}\n"
            f"Шаги: {[s.name for s in steps]}"
        )

    def test_build_steps_order(self):
        p = ChatInferencePipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация (через Gateway)",
            "Создание чат-сессии (через Gateway)",
            "Отправка сообщения (через Gateway)",
            "Текстовый поиск (через Gateway)",
            "Проверка enrichment_skipped (через Gateway)",
            "Поиск RAG Search",
        ]
        actual_names = [s.name for s in steps]
        assert actual_names == expected_names, f"Порядок шагов не совпадает:\n{actual_names}"

    def test_auth_steps_first(self):
        p = ChatInferencePipeline()
        steps = p.build_steps(PipelineContext())
        assert steps[0].service == "gateway"

    def test_needs_auth_after_auth(self):
        p = ChatInferencePipeline()
        steps = p.build_steps(PipelineContext())
        for step in steps[1:]:
            assert step.needs_auth, f"Шаг '{step.name}' должен требовать auth"

    def test_extract_keys(self):
        p = ChatInferencePipeline()
        steps = p.build_steps(PipelineContext())
        assert steps[0].extract_keys == ["access_token", "refresh_token"]
        assert steps[1].extract_keys == ["session_id"]
        assert steps[2].extract_keys == ["message_id"]


class TestRegistryLifecyclePipeline:
    """Пайплайн registry_lifecycle — 11 шагов."""

    def test_pipeline_attributes(self):
        p = RegistryLifecyclePipeline()
        assert p.name == "registry_lifecycle"
        assert p.description == "CRUD + импорт классификаторов и терминов"
        assert "gateway" in p.services
        assert len(p.services) == 2

    def test_build_steps_count(self):
        p = RegistryLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 11, (
            f"Ожидалось 11 шагов, получено {len(steps)}\n"
            f"Шаги: {[s.name for s in steps]}"
        )

    def test_build_steps_order(self):
        p = RegistryLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация (через Gateway)",
            "Профиль пользователя (через Gateway)",
            "Создать классификатор (через Gateway)",
            "Список классификаторов (через Gateway)",
            "Получить классификатор (через Gateway)",
            "Обновить классификатор (через Gateway)",
            "Частичное обновление классификатора (через Gateway)",
            "Удалить классификатор (через Gateway)",
            "Создать термин (через Gateway)",
            "Нормализация термина (через Gateway)",
            "Обновить термин (через Gateway)",
        ]
        actual_names = [s.name for s in steps]
        assert actual_names == expected_names, f"Порядок шагов не совпадает:\n{actual_names}"

    def test_crud_sequence(self):
        p = RegistryLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        classifier_steps = [s for s in steps if "классификатор" in s.name.lower()]
        assert len(classifier_steps) == 6
        methods = [s.method for s in classifier_steps]
        assert methods == ["POST", "GET", "GET", "PUT", "PATCH", "DELETE"], \
            f"CRUD-последовательность классификаторов: {methods}"

    def test_terminology_sequence(self):
        p = RegistryLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        term_steps = [s for s in steps if "термин" in s.name.lower()]
        assert len(term_steps) == 3
        methods = [s.method for s in term_steps]
        assert methods == ["POST", "GET", "PUT"], \
            f"Последовательность терминов: {methods}"

    def test_all_auth_required(self):
        p = RegistryLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        for step in steps[2:]:
            assert step.needs_auth, f"Шаг '{step.name}' должен требовать auth"


# ── Тесты реестра пайплайнов ──────────────────────────────────────────


class TestPipelineRegistry:
    """PIPELINE_REGISTRY — реестр всех 8 пайплайнов."""

    def test_registry_importable(self):
        from pipelines import PIPELINE_REGISTRY
        assert "document_processing" in PIPELINE_REGISTRY
        assert "chat_inference" in PIPELINE_REGISTRY
        assert "registry_lifecycle" in PIPELINE_REGISTRY
        assert "full_document_lifecycle" in PIPELINE_REGISTRY
        assert "admin_user_lifecycle" in PIPELINE_REGISTRY
        assert "registry_quarantine" in PIPELINE_REGISTRY
        assert "orchestrator_draft_lifecycle" in PIPELINE_REGISTRY
        assert "multi_document_cross_search" in PIPELINE_REGISTRY
        assert "document_approval" in PIPELINE_REGISTRY
        assert "orchestrator_document_reject" in PIPELINE_REGISTRY
        assert "orchestrator_metadata_update" in PIPELINE_REGISTRY
        assert "orchestrator_draft_delete" in PIPELINE_REGISTRY
        assert "orchestrator_document_reprocess" in PIPELINE_REGISTRY
        assert "orchestrator_document_versions" in PIPELINE_REGISTRY
        assert "orchestrator_full_document_lifecycle" in PIPELINE_REGISTRY
        assert len(PIPELINE_REGISTRY) == 16

    def test_registry_classes(self):
        from pipelines import PIPELINE_REGISTRY
        from pipelines.full_document_lifecycle import FullDocumentLifecyclePipeline
        assert PIPELINE_REGISTRY["full_document_lifecycle"] is FullDocumentLifecyclePipeline

    def test_registry_instantiation(self):
        from pipelines import PIPELINE_REGISTRY
        for name, cls in PIPELINE_REGISTRY.items():
            instance = cls()
            assert instance.name == name
            assert instance.description
            assert instance.services
