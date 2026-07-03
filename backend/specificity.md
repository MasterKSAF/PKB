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

## parser_docling

- **Docling StandardPdfPipeline** падает с "Input document is not valid" для PDF с нестандартной структурой (например, 2-020101-174-1.pdf).
  Fallback через DoclingPdfParser + docling-core работает.
- **pypdfium2 engine** — быстрый, но даёт один блок на страницу без разбивки на строки.
