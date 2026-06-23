# Todo — Реорганизация endpoints: чтение drafts/documents → Registry

> Создан: 23.06.2026
> Статус: В работе

## Контекст

Архитектурное решение (23.06): чтение черновиков и документов уходит из Orchestrator
в Registry. Orchestrator остаётся координатором пайплайна.

## Блоки

### 1. Документация — зафиксировать решение
- [x] `guide.md` — обновить п. 2.1: orchestrator не проксирует чтение Registry
- [x] `specificity.md` — добавить п. 2.6 с новым решением
- [x] `readme.md` — убрать GET /drafts, GET /drafts/{id} из таблицы; добавить GET /documents/{id}/tasks

### 2. Удалить read-эндпоинты черновиков из orchestrator
- [x] `drafts.py` — удалить `list_drafts` (`GET /drafts/`), `get_draft` (`GET /drafts/{draft_id}`)
- [x] `drafts.py` — очистить неиспользуемые импорты (DraftItem, DraftListResponse, DraftDetailResponse)
- [x] `schemas/drafts.py` — удалить `DraftItem`, `DraftListResponse`, `DraftDetailResponse`
- [x] `schemas/__init__.py` — очистить экспорт удалённых схем
- [x] `tests/test_drafts.py` — удалить TestListDrafts, TestGetDraft
- [x] `tests/test_health.py` — убрать проверки удалённых путей
- [x] `tests/test_monitor.py` — заменить GET /drafts на GET /drafts/1/tasks
- [x] `tests/integration/test_draft_to_version.py` — убрать шаг GET /drafts/{id}

### 3. Добавить GET /documents/{doc_id}/tasks
- [x] `schemas/tasks.py` — добавить `DocumentTasksResponse`
- [x] `documents.py` — добавить `GET /{doc_id}/tasks` endpoint
- [x] `tests/test_documents_api.py` — добавить тесты DocumentTasks

### 4. Финальный обзор
- [x] OpenAPI: `GET /api/v1/drafts/` и `GET /api/v1/drafts/{id}` отсутствуют
- [x] OpenAPI: `GET /api/v1/documents/{doc_id}/tasks` присутствует
- [x] `pytest` — 306 passed
- [x] Целостность: manage-эндпоинты черновиков не затронуты
- [x] Удалённые схемы не импортируются нигде
