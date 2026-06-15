# Todo — Orchestrator не проходит тесты в Docker

## Проблема
Оркестратор валится с 500 (step 6) и 422 (step 7) в pipeline `orchestrator_draft_lifecycle`.

## Причины

### 1. `get_preview_status` использовал локальную таблицу `drafts` вместо Registry
- В `get_preview_status()` был `from app.models.drafts import Draft` + `db.get(Draft, draft_id)` — проверка через локальную таблицу `public.drafts`
- Registry уже ведёт свою таблицу `registry.drafts` — оркестратор не должен дублировать
- Таблица `public.drafts` не создавалась → `UndefinedTableError`
- **Исправление:** заменён на HTTP-вызов `registry.get_draft(draft_id)`

### 2. Несоответствие полей запроса в `decide`
- Pipeline шлёт `{"decision": "approved", "comment": "..."}`
- API ожидает `{"action": "approve", "comment": "..."}`

## План

### Шаг 1: Импорт app.models в main.py
- [x] Добавить `import app.models` в `app/main.py` (lifespan startup)

### Шаг 2: Исправить pipeline шаг 7 (decide)
- [x] В `service_checker/pipelines/orchestrator_draft_lifecycle.py` исправить body на `{"action": "approve", "comment": "..."}`
- [x] В тесте `test_pipeline_orchestrator_draft_lifecycle.py` обновить expected_status (сейчас 200, 409 — 422 был workaround)

### Шаг 3: Проверить
- [x] `python -m pytest tests/ -v` в `service_checker` — 141 passed
- [x] `python -m pytest tests/ -v` в `orchestrator_service` — 351 passed, 1 pre-existing fail
- [x] `docker compose down --volumes && up -d` — полный сброс
- [x] `python -m service_checker docker --action full-report` — **Orchestrator: ✅ 8/8**
