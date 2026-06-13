# Todo — Исправление 4 замечаний Gateway — ВЫПОЛНЕНО ✅

## Результаты

### 1. Feedback в чате (замечание #1) ✅
- Добавлено поле `rating_status` в `FeedbackRequest`
- Добавлена валидация эксклюзивности `session_id` vs `answer_id` (400 AMBIGUOUS_FEEDBACK_FORMAT)
- Добавлена валидация `rating` (1–5) и `rating_status` (positive/negative/neutral)
- Тесты исправлены (разделены на 2 формата)
- Документация уже была корректна

### 2. Chat projects и сессии (замечание #2) ✅
- Добавлен `project_id: Optional[int]` в `UpdateSessionRequest`
- Хендлер `update_session` сохраняет `project_id` при обновлении
- Документация уже была корректна

### 3. GET /drafts — фильтр по draft_id + document_key опционально (замечание #7) ✅
- Добавлен опциональный параметр `draft_id` в `list_drafts`
- `document_key` сделан опциональным (был `default=""`, стал `Optional[str] = Query(None)`)
- Документация обновлена
- Тесты уже ожидали поведение 200 без document_key

### 4. Связь документов с разделами (замечание #8) ✅
- Добавлено поле `group` в SEED_DOCUMENTS и SEED_REGISTRY_DOCUMENTS
- Исправлен `mks_oks_code` документа 1: `"01.100"` → `"31.240"` (существует в классификаторах)
- Обновлён формат `classification_status` с `{"mks_status":...}` на `{"mks": [...], "okstu": [...], ...}`
- Добавлены `group`, `mks_name`, `okstu_name` в ответы `list_documents` и `get_document`
- Обновлены хендлеры `decide_draft`, `upload_document`
- Классификаторы уже содержат все нужные коды (47.020, 47.020.30, 31.240, 05.020, 12.000)

### 5. Замечание #5 (upload-by-url) — удалено
- Endpoint upload-by-url не реализован и не запланирован
- Загрузка документов работает через POST /drafts (multipart)

### 6. Валидация ✅
- **470 тестов проходят** (было 468, 2 упавших исправлены)
