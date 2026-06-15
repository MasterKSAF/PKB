"""Тесты определения шагов пайплайнов."""
from __future__ import annotations

import pytest

from service_checker.pipelines.base import PipelineContext, StepStatus
from service_checker.pipelines.document_processing import DocumentProcessingPipeline
from service_checker.pipelines.chat_inference import ChatInferencePipeline
from service_checker.pipelines.registry_lifecycle import RegistryLifecyclePipeline


class TestDocumentProcessingPipeline:
    """Пайплайн document_processing — 8 шагов."""

    def test_pipeline_attributes(self):
        p = DocumentProcessingPipeline()
        assert p.name == "document_processing"
        assert p.description == "Полный цикл обработки документа"
        assert len(p.services) == 7

    def test_build_steps_count(self):
        p = DocumentProcessingPipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 10, (
            f"Ожидалось 10 шагов, получено {len(steps)}\n"
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
            "Конвертация JSON",
            "Сохранение документа в Registry",
            "Построение чанков и индексация",
            "Поиск по индексу RAG Search",
        ]
        actual_names = [s.name for s in steps]
        assert actual_names == expected_names, f"Порядок шагов не совпадает:\nОжидалось: {expected_names}\nПолучено: {actual_names}"

    def test_build_steps_services(self):
        p = DocumentProcessingPipeline()
        steps = p.build_steps(PipelineContext())
        services = [s.service for s in steps]
        assert "auth" in services
        assert "minio" in services
        assert "parser" in services
        assert "converter_validator" in services
        assert "registry" in services
        assert "rag_builder" in services
        assert "rag_search" in services

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
        expected = [200, {200, 409}, 200, 202, 200, 200, 200, {201, 409}, {200, 201}, 200]
        actual = [s.expected_status for s in steps]
        assert actual == expected, f"Ожидаемые статусы не совпадают:\n{actual}"

    def test_steps_initial_status(self):
        p = DocumentProcessingPipeline()
        steps = p.build_steps(PipelineContext())
        for step in steps:
            assert step.status == StepStatus.PENDING, \
                f"Шаг '{step.name}' должен иметь статус PENDING"


class TestChatInferencePipeline:
    """Пайплайн chat_inference — 5 шагов (шаг профиля удалён — mock-режим auth)."""

    def test_pipeline_attributes(self):
        p = ChatInferencePipeline()
        assert p.name == "chat_inference"
        assert p.description == "Чат-сессия с поиском по проиндексированным документам"
        assert len(p.services) == 3

    def test_build_steps_count(self):
        p = ChatInferencePipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 5, (
            f"Ожидалось 5 шагов, получено {len(steps)}\n"
            f"Шаги: {[s.name for s in steps]}"
        )

    def test_build_steps_order(self):
        p = ChatInferencePipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация",
            "Создание чат-сессии",
            "Отправка сообщения",
            "Текстовый поиск",
            "Гибридный поиск RAG Search",
        ]
        actual_names = [s.name for s in steps]
        assert actual_names == expected_names, f"Порядок шагов не совпадает:\n{actual_names}"

    def test_auth_steps_first(self):
        p = ChatInferencePipeline()
        steps = p.build_steps(PipelineContext())
        # Первый шаг — аутентификация
        assert steps[0].service == "auth"

    def test_needs_auth_after_auth(self):
        p = ChatInferencePipeline()
        steps = p.build_steps(PipelineContext())
        # Шаги после аутентификации требуют токен
        for step in steps[1:]:
            assert step.needs_auth, f"Шаг '{step.name}' должен требовать auth"

    def test_extract_keys(self):
        p = ChatInferencePipeline()
        steps = p.build_steps(PipelineContext())
        assert steps[0].extract_keys == ["access_token", "refresh_token"]
        assert steps[1].extract_keys == ["session_id"]
        assert steps[2].extract_keys == ["message_id"]


class TestRegistryLifecyclePipeline:
    """Пайплайн registry_lifecycle — 13 шагов."""

    def test_pipeline_attributes(self):
        p = RegistryLifecyclePipeline()
        assert p.name == "registry_lifecycle"
        assert p.description == "CRUD + импорт классификаторов и терминов"
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
            "Аутентификация",
            "Профиль пользователя",
            "Создать классификатор",
            "Список классификаторов",
            "Получить классификатор",
            "Обновить классификатор",
            "Частичное обновление классификатора",
            "Удалить классификатор",
            "Создать термин",
            "Нормализация термина",
            "Обновить термин",
        ]
        actual_names = [s.name for s in steps]
        assert actual_names == expected_names, f"Порядок шагов не совпадает:\n{actual_names}"

    def test_crud_sequence(self):
        p = RegistryLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        # Проверка CRUD-последовательности для классификаторов
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
        for step in steps[2:]:  # После аутентификации
            assert step.needs_auth, f"Шаг '{step.name}' должен требовать auth"


# ── Тесты реестра пайплайнов ──────────────────────────────────────────


class TestPipelineRegistry:
    """PIPELINE_REGISTRY — реестр всех пайплайнов."""

    def test_registry_importable(self):
        from pipelines import PIPELINE_REGISTRY
        assert "document_processing" in PIPELINE_REGISTRY
        assert "chat_inference" in PIPELINE_REGISTRY
        assert "registry_lifecycle" in PIPELINE_REGISTRY
        assert len(PIPELINE_REGISTRY) == 3

    def test_registry_classes(self):
        from pipelines import PIPELINE_REGISTRY
        from pipelines.document_processing import DocumentProcessingPipeline
        assert PIPELINE_REGISTRY["document_processing"] is DocumentProcessingPipeline

    def test_registry_instantiation(self):
        from pipelines import PIPELINE_REGISTRY
        for name, cls in PIPELINE_REGISTRY.items():
            instance = cls()
            assert instance.name == name
            assert instance.description
            assert instance.services
