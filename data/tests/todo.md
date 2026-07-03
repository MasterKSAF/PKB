# Тестирование загрузки документов и дублей

## Результаты проверки (2026-07-03)

### 1. Конкурентный тест всех PDF из data/pdf_tests (7 файлов)
- **Файл**: `test_pdf_tests_full.py` — 7 фаз: Upload → Preview → Approve → Pipeline → Search → Order → Duplicate
- **Upload**: 7/7 OK
- **Preview**: 7/7 OK (исправлено: 409 при авто-обработке трактуется как OK)
- **Pipeline**: 1/7 completed (только `2-020101-174-19.pdf`), 6/7 падают на `registry_creation`
- **Search**: 1/1 найден (для завершённого документа)
- **Order errors**: 0
- **Duplicate detection**: PASS

### 2. Bulk Upload — все 63 PDF из data/pdf/
- `test_bulk_upload.py`: 63/63 — 100% успешно (HTTP 202)

### 3. Последовательная загрузка (rate limiting)
- `test_go.py`: 7/7 PDF из pdf_tests — HTTP 202, без 429

### 4. Pipeline Registry → Orchestrator → RAG Builder (СЛОМАН)
- `run_registry_step` вызывает `POST /api/v1/registry/documents` → **400 Bad Request**
- Причина: `create_pipeline_document` ожидает `document.metadata.title` и `document.metadata.doc_code`, но конвертер отдаёт другой формат
- Registry не сохраняет секции → Orchestrator не может их прочитать → RAG Builder не получает данные
- Статус документа остаётся "uploaded" вместо "validating"

### 5. Duplicate check (НЕ РАБОТАЕТ для новых документов)
- `test_dup_check.py` падает с `File not found` (путь относительный)
- `check_document_uniqueness` проверяет только таблицу `Document`, не `Draft`
- Но тест `test_pdf_tests_full.py` (Phase 8) показывает duplicate detection PASS при повторной загрузке того же файла

### Исправлено
- `test_pdf_tests_full.py` — `start_preview_single` принимает HTTP 409 как "уже запущен" (оркестратор авто-обрабатывает после upload)
