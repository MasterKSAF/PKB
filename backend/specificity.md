# Аномалии и специфические моменты

## Auth Service

- **init_db** обновляет permissions существующих ролей при перезапуске (с версии, когда это было добавлено).

## Registry Service

- **check_document_uniqueness** проверяет дубликаты только в таблице Document, не проверяет Drafts. Поле `is_duplicate_file` всегда `False` — дубли на уровне файла не детектятся.
- **create_pipeline_document** (POST /api/v1/registry/documents) ожидает формат `{document: {metadata: {title, doc_code, ...}, content: [...]}}`, но конвертер из pipeline присылает другой формат. Ошибка 400 при попытке сохранить документ из pipeline.
- **http_exception_handler** принудительно транслирует 422 → 400 для VALIDATION_ERROR, что маскирует оригинальный код ошибки.

## Pipeline

- **registry_creation** шаг падает с 400 из-за несовпадения формата данных между конвертером и create_pipeline_document.
- **Секции не сохраняются** → Orchestrator не может прочитать sections с ID → RAG Builder не получает данные для индексации.
- Статус документа после approve остаётся "uploaded" (не доходит до "validating").
- **FULL_PHASE_MODE="full"** пропускает Parser/OCR на full-фазе полностью. При `full_completed=False` документ уходит в Converter без распознанного текста.
  Guard: добавлен warning-лог в approve_draft при `full` mode + `full_completed=False`.
- **После approve Celery-задачи могут не выполняться**, если нет воркеров (docker без celery -pipeline). Документ создаётся в Registry со статусом "uploaded", но pipeline (ocr→converter→registry→rag) не завершается.
  Тесты не ловят это, т.к. мокают .delay() глобально.

## Parser → Converter / Orchestrator

- **Поле страницы в блоках**: `html_to_json.py` и `md_to_json.py` пишут `"page number"` в блоки, но `hierarchy_builder.py:81` читает `block.get("page")`, а `pipeline_formation.py:368` читает `b.get("page", 1)`. Поле `"page"` появляется в блоках только после прохода `standardizer.py`. При передаче сырого `raw_json` (не стандартизированного) все блоки получают `page=1`.
  - Починено: `hierarchy_builder.py:81` и `pipeline_formation.py:368` читают `block.get("page") or block.get("page number") or 1`.

### Почему черновик сразу в "uploaded" после подтверждения (2026-07-05)

**Сценарий:**
1. UI отправляет PATCH /drafts/{id}/decide action=approve
2. `approve_draft()` создаёт документ в Registry с `status: "uploaded"` (строка 1277 orchestrator.py)
3. Диспатчит Celery-задачи full_ocr/full_converter/registry/rag в очередь
4. **Если нет Celery worker — задачи висят в очереди**, документ навсегда остаётся "uploaded"
5. Даже если Celery есть, **registry_creation шаг падает с 400** из-за несовпадения формата данных

**Почему тесты не ловят:**
- Все .delay() замоканы глобально в conftest.py (no-op)
- Тесты проверяют HTTP-ответ (200, document_id есть), но не проверяют что Celery-задачи реально диспатчатся
- Нет E2E-теста, который бы запускал Celery worker воркер и проверял pipeline до конца

**Что делать:**
- Временно: запустить celery -A app.celery_app worker -Q pipeline в отдельном контейнере
- Постоянно: интеграционный тест, который проверяет что после approve задача переходит в active/full_stage

## parser_docling

- **Docling StandardPdfPipeline** падает с "Input document is not valid" для PDF с нестандартной структурой (например, 2-020101-174-1.pdf).
  Fallback через DoclingPdfParser + docling-core работает.
- **pypdfium2 engine** — быстрый, но даёт один блок на страницу без разбивки на строки.
