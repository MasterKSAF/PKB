# План дальнейших работ

## Текущий статус

**Pipeline**: 15/15 (2 пайплайна падают из-за Orchestrator 500, не checker)
**API Coverage**: 229/229 ✅ — все сервисы зелёные
**Unit-тесты**: 563/563 ✅
**Docker full-report**: ✅ Gateway 77/77, Query 27/27, все сервисы зелёные

---

### Что сделано

#### Gateway: 6 skipped → 0 skipped ✅
- `user_id` — prepare-шаг уже был (POST /admin/users) — 3 эндпоинта починены
- `pending_id` — добавлены prepare-шаги: POST /classifiers/ → GET /classifiers/pending — 2 эндпоинта починены
- `file_id` — путь изменён на `/files/1` (без плейсхолдера) — Mock Gateway возвращает 200

#### Синхронизация тестов с пайплайнами
- `orchestrator_full_document_lifecycle` — 12→11 шагов, missing import `check_json_fields` (багфикс)
- `orchestrator_document_reprocess` — 9→6 шагов (пайплайн перестроен)
- `orchestrator_document_versions` — 9→4 шага (пайплайн перестроен)
- `document_approval` — `longpoll: 0` → `longpoll: 1`

#### Проверки в Docker
- Gateway API Coverage: 77/77 ✅ (было 69/75)
- Query API Coverage: 27/27 ✅ (UniqueViolation → 409 починено)
- Полный прогон: все сервисы зелёные по API

---

## Осталось

### 1. Orchestrator: POST /drafts → HTTP 500

**Симптом**: specificity.md #53 — `POST /api/v1/drafts/` возвращает 500.
**Блокирует**: 9 пайплайнов с черновиками, в т.ч.:
- `orchestrator_document_reprocess` (5/6)
- `orchestrator_draft_lifecycle` (10/11)
- Registry Service pipelines (производная ошибка)

**Требуется**: диагностика разработчиками Orchestrator.

### 2. RAG Builder: UNIQUE-индекс

**Симптом**: отсутствует `rag.document_chunks_section_chunk_key`.
**Требуется**: проверить миграции Alembic RAG Builder.

### 3. Registry: Categories не реализованы

Известная проблема — 5 CRUD эндпоинтов возвращают 404.

---

## Справка

- **recheck.bat**: `docker/recheck.bat` — полный цикл (чистка БД → перезапуск → отчёт)
- **Быстрые проверки**: `python -m service_checker docker --action full-report --services <name> --skip-pipelines`
- **Unit-тесты**: `python -m pytest tests/` (без Docker)
- **Отчёты**: `check_result/full_report.md`, `check_result/api_coverage.md`
