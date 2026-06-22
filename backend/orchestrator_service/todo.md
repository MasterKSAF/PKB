# Todo — Удаление GET /documents/* из оркестратора

> Создан: 22.06.2026
> Режим: real (по умолчанию), mock только для тестов

## Контекст

`GET /documents/*` (list, get, status, file, history, errors, parameters, queue, pages/*) перенесены в `registry-service` (см. `docs/api/registry_service_api.md`, группа `documents`).

В оркестраторе должны остаться только:
- `POST /drafts`, `GET /drafts*`, `PATCH /drafts/{id}/decide`, `DELETE /drafts/{id}` — управление черновиками
- `GET /tasks*`, `GET /tasks/{id}/steps`, `GET /tasks/stats` — мониторинг пайплайнов
- `GET /system/health`, `GET /health/live`, `GET /health/ready` — health-check
- `POST /documents/{id}/reprocess` (P2I-9) — pipeline-операция переиндексации, остаётся в оркестраторе
- `GET /drafts/{id}/tasks` — список задач черновика

## Блоки

### 1. Ориентиры и аномалии
- [ ] Зафиксировать архитектурное решение в `guide.md`
- [ ] Записать в `specificity.md` (раздел «Расхождения»)

### 2. Удаление GET /documents/* из кода
- [ ] Перезаписать `app/api/v1/endpoints/documents.py` — оставить только `POST /{doc_id}/reprocess`
- [ ] Почистить `app/schemas/documents.py` — оставить только `ReprocessRequest`, `ReprocessResponse`, `ReprocessMode`
- [ ] Обновить импорты в `api.py` (если потребуется)

### 3. Тесты
- [ ] `tests/test_documents_api.py` — удалить классы TestVersionCreate, TestVersionsList, TestApproveDocument, TestDocumentHistory, TestListDocuments, TestDocumentQueue, TestGetDocument, TestDocumentStatus, TestDocumentFile, TestDocumentPages, TestDocumentPageView, TestDocumentPageText, TestDocumentPagePreview, TestDocumentErrors, TestDocumentParameters. Оставить только TestDocumentReprocess.
- [ ] `tests/test_health.py::test_openapi_has_all_paths` — убрать проверку `/api/v1/documents/`
- [ ] `tests/test_error_handling.py::test_documents_search_no_longer_returns_search_results` — переименовать/обновить под новую реальность
- [ ] Прогнать `pytest`, добиться 100% pass

### 4. Документация
- [ ] `docs/api/orchestrator_service_api.md` — убрать группу `documents` (GET endpoints), оставить только `POST /documents/{doc_id}/reprocess` (если оставляем в этом файле)
- [ ] `readme.md` — убрать из таблицы endpoints все GET /documents/*, кроме reprocess
- [ ] `docs/README.md` — убрать ссылки на перенесённые endpoints

### 5. Финальный обзор
- [ ] Проверить, что orchestrator больше не отдаёт GET /documents/* в OpenAPI
- [ ] Проверить целостность (drafts + tasks + health + reprocess)
- [ ] Проверить, что ничего не сломалось в pipeline (reprocess, formation, indexation)
- [ ] Проверить correlation-headers и OTEL не задеты
