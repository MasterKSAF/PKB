# ✅ Выполнено: правки чекера (2026-06-10)

## 1. `core/db_check.py` — предупреждение read-only
- Добавлено в docstring: модуль только проверяет БД (SELECT), не изменяет её

## 2. `pipelines/document_processing.py` — починка пути к PDF
- Путь `pdf/7bd97d737317a8a272bb18a405ab2d04.pdf` был относительным от CWD
- При запуске из `recheck.bat` (CWD = `backend/`) файл не находился
- Исправлен на абсолютный через `Path(__file__).resolve().parent.parent / "pdf" / ...`

## 3. Все id — только int (убраны `(int, str)`)

### response_schema (int вместо (int, str)):
- `services/auth.py` — `id`
- `services/converter_validator.py` — `task_id`, `version_id`, `document_id`, `validation_id`
- `services/orchestrator.py` — `task_id`, `document_id`, `draft_id`
- `services/parser.py` — `task_id`
- `services/ocr.py` — `task_id`
- `services/rag_builder.py` — `document_id`
- `services/registry.py` — `document_id`, `version_id`, `id`

### body (строки → int):
- `services/converter_validator.py`, `parser.py`, `ocr.py` — `task_id: 12345`
- `services/rag_builder.py` — `document_id: 1`

### pipelines (строки → int):
- `pipelines/chat_inference.py` — `session_id`, `message_id`: `int` (check)
- `pipelines/document_processing.py` — `TEST_TASK_ID: 12345`, `document_id: 1`

## 4. Проверка целостности
- `(int, str)` полностью удалён из всех `.py` файлов
- `api_coverage_test.py` — проверка `isinstance(value, expected_type)` теперь корректна
- 116 тестов проходят

## Остаётся
- Registry и RAG Builder не имеют `create_all()` в startup (известная проблема)
- При полном запуске Docker `db-check` покажет ❌ для RAG таблиц
