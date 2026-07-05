# Specificity — аномалии и трудные моменты

## ⚙ Особенности рабочего окружения

### G7. Pipeline: preview status не приходит в completed (дублирующиеся шаги)

**Симптом:** `GET /drafts/{id}/preview/status` возвращает `"status":"processing"` даже когда preview выполнен.

**Причина:** `on_step_completed` вызывается дважды для `preview_converter` (из-за дублирующихся задач Celery).
Создаются два шага с `step_name="preview_converter"` — один completed, второй pending.
`_build_preview_status` проверяет `all(s.status == "completed" for s in preview_steps)` → всегда False.

**Где:** `backend/orchestrator_service/app/api/v1/endpoints/drafts.py`, функция `_build_preview_status`.

**Статус:** не исправлено.

### G8. Pipeline: registry_creation падает с `compensations applied`

**Симптом:** `Pipeline failed at step registry_creation, compensations applied`.
6 из 7 PDF (тест `test_pdf_tests_full.py`) падают на этом шаге. Только 1 из 7 (`2-020101-174-19.pdf`) проходит.

**Причина:** `create_pipeline_document` вызывает `POST /api/v1/registry/documents` с неверным форматом данных — конвертер отдаёт поля не в той структуре, которую ожидает Registry (ожидает `document.metadata.title`, `document.metadata.doc_code`).

**Где:** `backend/orchestrator_service/app/core/pipeline/orchestrator.py` — `_create_registry_document`.

**Статус:** не исправлено.

### B3. RAG-индексация не стартует даже при доступных данных

**Симптом:** Данные в RAG Search уже есть (поиск находит doc_id=59),
но pipeline висит на 99%, `rag_index` всегда `pending`.

**Причина:** rag_index стартуется только через цепочку:
`full_ocr completed → _on_full_step_completed → enqueue full_converter →
full_converter completed → enqueue registry_creation →
registry_creation completed → enqueue rag_index`

Если любой шаг в цепочке не завершён (B2: full_ocr running) — rag_index никогда не стартует.
При этом RAG Builder может получить данные другим путём (через auto-индексацию или
параллельный процесс), поэтому данные в поиске есть, но pipeline не в курсе.

**Где:** `PipelineOrchestrator._on_full_step_completed()` (orchestrator.py:714–842).

### D1. Детекция дублей — ЧАСТИЧНО (01.07)

**Upload-уровень:** HTTP 409 с `DUPLICATE_IN_PROGRESS` на повторную загрузку — РАБОТАЕТ.
Подтверждено на `2-020101-004.pdf` и `gost_22786-77.pdf`.

**Registry-уровень (документы):** НЕ РАБОТАЕТ — все `file_hash_sha256` пустые (NULL).
- `approve_draft()` не передаёт `file_hash_sha256` в `registry.create_document(doc_payload)`
- В `registry.drafts` нет колонки `file_hash_sha256` (хотя RegistryServiceClient.create_draft() принимает параметр)
- PostgreSQL UNIQUE constraint на `file_hash_sha256` пропускает множественные NULL
- **Следствие:** каждый approve создаёт новый document, дубли множатся

**Где чинить:**
1. `backend/orchestrator_service/app/core/pipeline/orchestrator.py` — `approve_draft()`: добавить `file_hash_sha256` в `doc_payload`
2. `backend/orchestrator_service/app/services/registry_client.py` — `create_draft()`: убедиться что `file_hash_sha256` сохраняется в черновике

### S1. Search 500 — bbox строка вместо списка (30.06, НОВАЯ)

**Статус:** НЕ ИСПРАВЛЕНО

**Симптом:** `POST /api/v1/rag/search` → HTTP 500: `Input should be a valid list [type=list_type, input_value='[0.255, 0.595, 0.786, 0.631]', input_type=str]`

**Корневая причина:** Конвертер/парсер сериализует `bbox` как JSON-строку, Pydantic ожидает list.

**Где должно быть:**
- Конвертер должен передавать `bbox` как список чисел, а не строку
