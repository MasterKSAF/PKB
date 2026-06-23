# План исправления — итерация

## Статус (2026-06-23, recheck)

**Pipeline**: 15 пайплайнов
- ✅ 6 пройдено (Registry, Auth, Чат, Полный lifecycle, Multi-doc)
- ❌ 9 падают (частичный прогресс)
- DB Check: схемы auth, pipeline ✅ (были ❌)
- DB Check: UNIQUE индексы ❌ (не трогали Registry)

---

## ✅ БЛОК 1: P0 — Orchestrator → Registry 422 (исправлено)

### 1a. POST /registry/drafts — missing `status`
- `CreateDraftRequest` + `status: str = "uploaded"`

### 1b. POST /registry/documents/check-uniqueness — wrong body
- `CheckUniquenessRequest` → правильные поля (title, doc_code, era, source_type)
- `check_uniqueness()`, `_mock_check_uniqueness()` обновлены

### 1c. Registry возвращает `id`, а не `draft_id`
- `drafts.py` — чтение `id` вместо `draft_id` из ответа Registry
- Мок `create_draft` возвращает `"id"` (соответствует Registry)

**Результат**: POST /drafts → 202 ✅, draft_id корректный

---

## ✅ БЛОК 2: P0 — DB схемы (исправлено)

### 2a. Схема `auth`
- `auth_service`: `search_path = auth`, `CREATE SCHEMA IF NOT EXISTS auth`

### 2b. Схема `pipeline`
- Модели оркестратора: `schema="pipeline"`
- `main.py`: создание схемы при старте
- `conftest.py`: ATTACH для SQLite

**Результат**: схемы auth, pipeline создаются ✅

---

## ✅ БЛОК 3: P1 — RAG Builder миграции (исправлено)

- Удалены 5 старых Alembic миграций
- Создана единая `20260623_0001_consolidated_rag_schema.py`
- Из модели убран `UniqueConstraint(section_id, chunk_index)`
- Из checker'а убран DROP UNIQUE workaround (оставлен только DROP FK)

---

## ❌ Текущие падения (pre-existing)

### Orchestrator API: 7 failed, 14 skipped

Что конкретно падает в API Coverage (нужен детальный разбор):
- `GET /tasks/{task_id}/status` — 404 (эндпоинт не найден)
- `GET /drafts/{draft_id}` — 405 (Method Not Allowed)
- `PATCH /drafts/{draft_id}/decide` — 409 approve ("Поле 'status' не найдено")
- `PATCH /drafts/{draft_id}/metadata` — 404 (не зарегистрирован?)
- `GET /tasks/stats` — вероятно, та же проблема
- 14 skipped — не хватает prepare-данных (из-за падений выше)

**Нужно**: разобрать каждый failed endpoint и починить регистрацию роутов в оркестраторе.

### Registry: 2 failed, 3 skipped
- Categories (7 CRUD) — не реализованы (известно)
- Связано с падениями оркестратора (не хватает prepare-данных)

### DB: UNIQUE индексы Registry (4 шт)
- Отложено — ждём готовности Registry для правок

---

## 📋 План дальнейших действий

### P0: Починить Orchestrator API (7 failed)
1. `GET /tasks/{task_id}/status` — проверить регистрацию роута
2. `GET /drafts/{draft_id}` — 405 → возможно GET не зарегистрирован (есть только POST, DELETE, PATCH)
3. `PATCH /drafts/{draft_id}/decide` — 409 approve (проблема с ответом Registry)
4. `PATCH /drafts/{draft_id}/metadata` — 404 → проверить эндпоинт
5. Остальные 3 failed + 14 skipped (раскроются после починки основных)

### P1: Registry — 4 UNIQUE индекса
- Добавить `UniqueConstraint` в модели `document.py` и `document_versions.py`

### P2: Registry — preview_snapshot
- `GET /documents/{id}` не возвращает `preview_snapshot`

### P3: Registry — Categories CRUD
- Реализовать 7 эндпоинтов для `/api/v1/registry/categories/*`

### P4: OpenTelemetry
- Запустить signoz-otel-collector
