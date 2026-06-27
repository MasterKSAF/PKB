# Todo: Fix 2 xfail bugs

## Статус: 🚧 НАЧАТО

## Баг 1: approve_draft не синхронизирует document_id с Registry

**Где:** `app/core/pipeline/orchestrator.py` → `approve_draft()`

**Проблема:** `approve_draft` создаёт документ через `Registry.create_document()`,
но НЕ вызывает `registry.update_draft_status(document_id=document_id)`, чтобы
проставить `document_id` обратно в черновик Registry.

**Исправление:** после `create_document()` → вызвать `update_draft_status(draft_id, status="approved", document_id=document_id)`

**Файлы:**
- `app/core/pipeline/orchestrator.py` — добавить вызов update_draft_status в approve_draft
- `tests/orchestrator/test_drafts_consistency.py` — снять `pytest.xfail()`, тест должен проходить

---

## Баг 2: `data.get("id") or data.get("draft_id")` — 0 is falsy

**Где:** эндпоинты, которые проксируют ответ Registry и используют `data.get("id") or data.get("draft_id")`

**Проблема:** если `id=0` (реальное значение), то `0 or ...` вернёт `...`, а не 0.
В mock-тестах `id` проставляется в 0, `draft_id` отсутствует → результат None.

**Исправление:** заменить `data.get("id") or data.get("draft_id")` на `data.get("id") if data.get("id") is not None else data.get("draft_id")`

**Файлы:**
- `app/...` — найти все вхождения паттерна `data.get("id") or data.get("draft_id")` и исправить
- `tests/orchestrator/test_drafts_consistency.py` — снять `pytest.xfail()`, тест должен проходить
