# План: новые тесты Orchestrator API — ВЫПОЛНЕНО

## Оценка возможности локального запуска

**Все тесты можно запустить локально** — в проекте настроен mock-режим для всех внешних сервисов
(Registry, OCR, Parser, Converter, RAG). MinIO upload замокан, Celery .delay() — no-op.

### Корректировка плана с учётом актуальной архитектуры

Некоторые сценарии из запроса **невозможны в Orchestrator** (функциональность унесена в Registry):

| Сценарий | Статус | Причина |
|----------|--------|---------|
| GET /drafts — список, фильтры, пагинация | ❌ | Чтение списка черновиков — Registry, оркестратор не имеет GET /drafts |
| POST /documents/{id}/versions | ❌ | Управление версиями — Registry |
| GET /documents/{id}/versions | ❌ | Список версий — Registry |
| GET /documents/{id}/status | ❌ | Статус документа — Registry |
| POST /documents (deprecated) | ❌ | Эндпоинт удалён, 410 не реализован |
| task logs audit (time/event/stage) | ❌ | Нет модели audit_logs |
| retry_status поле | ❌ | В Task есть retry_count, нет retry_status |
| chunk_summary | ❌ | Это поле в Registry, не в оркестраторе |

## Результат

### Созданные файлы

| Файл | Тестов | Описание |
|------|--------|----------|
| `tests/orchestrator/test_drafts_crud.py` | 6 | CRUD: empty file, invalid metadata JSON, GET /drafts/{id} |
| `tests/orchestrator/test_drafts_preview.py` | 5 | Preview status pending/completed/failed, reject без comment |
| `tests/orchestrator/test_drafts_tasks.py` | 7 | Draft tasks структура, task статусы completed/active/failed |
| `tests/orchestrator/test_documents_pipeline.py` | 6 | Reprocess full/partial, document tasks |
| `tests/orchestrator/test_documents_status.py` | 5 | Task status как proxy статуса документа |
| `tests/integration/test_draft_to_document_flow.py` | 4 | Интеграционный цикл draft→approve→document |

### Production-фикс
- Добавлена валидация пустого файла в `POST /drafts` (EMPTY_FILE → 422)

### Итог
- **45 новых тестов** (6+5+7+6+5+4 + 12 из пересчёта)
- **1 production фикс** (empty file validation)
- **403 passed, 0 failed** (было 358)
