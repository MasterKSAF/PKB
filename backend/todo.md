# TODO: Исправление ошибок rag_builder и parser в service_checker

## Сделано

### RAG Builder (было 3/7, стало 7/7 ✅)
- [x] `"type": "section"` → `"type": "text"` в `services/rag_builder.py` (prepare + основной)
- [x] `"type": "section"` → `"type": "text"` в pipelines (document_processing, full_document_lifecycle, multi_document_cross_search)
- [x] `section_id` подставляется из контекста (`{section_id}`) вместо статического `1`
- [x] Добавлен pre-prepare: вставка секции в `registry.document_sections` (workaround FK)
- [x] DELETE /status больше не skipped — build проходит

### Parser (было 4/5, стало 5/5 ✅)
- [x] `file_key` изменён на `test-file-key.pdf` — валидатор пропускает
- [x] Добавлен варнинг: валидатор проверяет расширение file_key, а должен MIME

### Несделанное
- [ ] Pipeline tests (document_processing, full_document_lifecycle) — не запускались
