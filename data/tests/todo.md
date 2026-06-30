# Тестирование загрузки документов и дублей

## План

1. **Загрузка PDF из data/pdf через корневой docker-compose**
   - `2-020101-004.pdf` — проверить upload + preview
   - `gost_22786-77.pdf` — проверить upload + preview

2. **Проверка дублей**
   - `test_dup_check.py` — загрузить один PDF дважды и проверить детекцию дубля
   - Сейчас `check_document_uniqueness` в Registry не проверяет DRAFTS (только DOCUMENTS), `is_duplicate_file` всегда False

3. **Проверка Registry → Orchestrator → RAG Builder (секции с ID)**
   - После approve: Registry сохраняет документ, генерирует section_id
   - Orchestrator читает sections обратно через `get_document_sections`
   - Передаёт в `run_rag_index_step` с `section_id` и `document_id`
   - Проверить через `test_universal_pdf_loader.py` или `test_full_pipeline.py`

4. **Выводы**
   - Что работает, что нет
   - Аномалии в specificity.md
