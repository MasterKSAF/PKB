# План правок — новые фиксы API + сверка с документацией

## Выполненный этап — Pipeline fixes (2026-06-20)

### [x] 1. `document_processing.py` — новые поля в body
- [x] 1.1 Парсинг: +`draft_id: 1` (PS-3)
- [x] 1.2 Конвертация: +`version_id: "1"` (CV-9)
- [x] 1.3 Registry: +`source_draft_id`, `mks_oks_code`, `title_key` (RG-9, DB-9, DB-28)

### [x] 2. `chat_inference.py` — новые поля + tolerant checks
- [x] 2.1 Создание сессии: +`document_ids`, `project_id` (QS-3)
- [x] 2.2 enrichment_skipped: tolerant check (QS-8)
- [x] 2.3 Текстовый поиск: убран `top_k` (RS-6)

### [x] 3. `orchestrator_draft_lifecycle.py` — дополнительные проверки
- [x] 3.2 Детали черновика: проверка `document_id`, `version_id`, `is_new_document` (OR-7)

### [x] 4. `full_document_lifecycle.py` — новые поля + статусы
- [x] 4.1 Создание документа: +`source_draft_id`, `mks_oks_code`, `title_key`
- [x] 4.2 build steps: 200/201 → 200/202 (RB-7)
- [x] 4.3 Обновление метаданных: `status` → `processing_status` (RG-1)

### [x] 5. `admin_user_lifecycle.py` — новые поля + tolerant статус
- [x] 5.1 Создание сессии: +`document_ids`, `project_id` (QS-3)
- [x] 5.2 Проверка блокировки: +401 в expected_status (AU-3)

### [x] 6. `multi_document_cross_search.py` — новые поля + статусы
- [x] 6.1 Парсинг #1/#2: +`draft_id: 1` (PS-3)
- [x] 6.2 Конвертация #1/#2: +`version_id: "1"` (CV-9)
- [x] 6.3 Registry #1/#2: +`source_draft_id`, `mks_oks_code`, `title_key`
- [x] 6.4 Build #1/#2: 200/201 → 200/202 (RB-7)

### [x] 7. Документация
- [x] 7.1 todo.md — актуализация
- [x] 7.2 specificity.md — запись об изменениях

## Новый этап — API Fixes + сверка с документацией (2026-06-20)

### [x] 1. RAG Builder — секции без document_id
- [x] 1.1 `docs/api/rag_builder_service_api.md` — убрать `document_id` из полей sections[]
- [x] 1.2 `services/rag_builder.py` — убрать `document_id` из секций в body
- [x] 1.3 `pipelines/document_processing.py` — убрать `document_id` из секций
- [x] 1.4 `pipelines/full_document_lifecycle.py` — убрать `document_id` из секций
- [x] 1.5 `pipelines/multi_document_cross_search.py` — убрать `document_id` из секций
- [x] 1.6 `services/rag_builder.py` — проверить response_schema для ответа 202

### [x] 2. RAG Search — сверка с RS-6
- [x] 2.1 `docs/api/rag_search_service_api.md` — соответствует RS-6: query/valid_at/filters, без search_type/top_k/rerank/version_id
- [x] 2.2 `services/rag_search.py` — body/response_schema соответствуют

### [x] 3. Query Service — плоские sources
- [x] 3.1 `docs/api/query_service_api.md` — sources без chunk_id/mode, плоская структура ✅
- [x] 3.2 `services/query.py` — body/response_schema в порядке

### [x] 4. Pipeline 3 — валидация по индексу sources
- [x] 4.1 Создать `check_rag_search_results` — проверка source (document_id + section_id) в ответах RAG Search
- [x] 4.2 `pipelines/base.py` — добавить функцию проверки по источнику
- [x] 4.3 `pipelines/full_document_lifecycle.py` — использовать валидацию по sources
- [x] 4.4 `pipelines/multi_document_cross_search.py` — использовать валидацию по sources
- [x] 4.5 `pipelines/document_processing.py` — использовать валидацию по sources
- [x] 4.6 `pipelines/chat_inference.py` — использовать валидацию по sources

### [x] 5. Тесты
- [x] 5.1 Тест для check_rag_search_results (11 кейсов)
- [x] 5.2 Обновить тесты пайплайнов, если нужно
- [x] 5.3 Проверить coverage

### [x] 6. Документация
- [x] 6.1 readme.md — актуальна (изменения не затрагивают readme)
- [x] 6.2 specificity.md — §44: записаны изменения
