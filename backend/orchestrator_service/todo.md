# Todo — Исправление mock-ответов RegistryServiceClient под реальные API

## Контекст
Все mock_response в RegistryServiceClient не соответствуют формату реальных ответов Registry API.
Из 12 endpoint'ов 5 имеют критические расхождения (без `data`, другие имена полей).

## План

### Phase 1: Исправление mock-методов (_mock_*)
- [x] 1. `_mock_create_document` — без `data` для pipeline-формата (есть `document` в payload)
- [x] 2. `_mock_get_document_sections` — без `data`
- [x] 3. `_mock_update_draft_status` — `draft_id`→`id`, +`previous_status`, -`document_id`
- [x] 4. `_mock_update_draft_metadata` — `draft_id`→`id`
- [x] 5. `_mock_delete_draft` — `draft_id`→`id`, -`deleted`

### Phase 2: Исправление публичных методов (mock_response + нормализация)
- [x] 6. `create_document` — нормализация уже есть, mock_response оставлен
- [x] 7. `get_document_sections` — mock_response без `data`, добавлена нормализация
- [x] 8. `update_draft_status` — mock_response с `id`, `previous_status`
- [x] 9. `update_draft_metadata` — mock_response с `id`
- [x] 10. `delete_draft` — mock_response с `id`, без `deleted`

### Phase 3: Обновление тестов
- [x] 11. Исправлены тесты: `test_update_draft_status_with_document_id`, `test_delete_draft`
- [x] 12. Проверена регрессия: 686 passed, 0 failed

### Phase 4: Документация
- [x] 13. Зафиксировать изменения в specificity.md (раздел 2.6)
