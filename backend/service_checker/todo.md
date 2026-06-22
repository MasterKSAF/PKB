# TODO: 6 новых пайплайнов оркестратора + тесты

## Подготовка
- [x] Создать план в todo.md

## 1. orchestrator_document_reject — Reject черновика
- [x] Создать `pipelines/orchestrator_document_reject.py`
- [x] Создать `tests/test_pipeline_orchestrator_document_reject.py`

## 2. orchestrator_metadata_update — Обновление метаданных
- [x] Создать `pipelines/orchestrator_metadata_update.py`
- [x] Создать `tests/test_pipeline_orchestrator_metadata_update.py`

## 3. orchestrator_draft_delete — Удаление черновика
- [x] Создать `pipelines/orchestrator_draft_delete.py`
- [x] Создать `tests/test_pipeline_orchestrator_draft_delete.py`

## 4. orchestrator_document_reprocess — Переиндексация
- [x] Создать `pipelines/orchestrator_document_reprocess.py`
- [x] Создать `tests/test_pipeline_orchestrator_document_reprocess.py`

## 5. orchestrator_document_versions — Версионирование
- [x] Создать `pipelines/orchestrator_document_versions.py`
- [x] Создать `tests/test_pipeline_orchestrator_document_versions.py`

## 6. orchestrator_full_document_lifecycle — Полный сквозной цикл через оркестратор
- [x] Создать `pipelines/orchestrator_full_document_lifecycle.py`
- [x] Создать `tests/test_pipeline_orchestrator_full_document_lifecycle.py`

## Регистрация и обновление
- [x] Зарегистрировать в `pipelines/__init__.py`
- [x] Обновить `core/config.py` (PIPELINE_SERVICE_MAP, PIPELINE_SERVICE_COLUMNS)
- [x] Обновить `readme.md`

## Проверка
- [x] Запустить все тесты — 533 passed
- [x] Добавить отдельную таблицу Orchestrator Pipelines в `core/reports.py`
- [x] Финальный обзор (см. ниже)
