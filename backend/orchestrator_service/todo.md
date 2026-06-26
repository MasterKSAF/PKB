# Todo: тест сохранения и извлечения метаданных

## Статус: ✅ ВЫПОЛНЕНО

- [x] Исправлен `_mock_get_draft_preview` — использует `metadata_fields` из хранилища
- [x] Добавлена маршрутизация `PATCH /{id}/metadata` в `_generate_mock`
- [x] Добавлен метод `_mock_update_draft_metadata`, сохраняющий данные в storage
- [x] Написаны 5 тестов в `TestMetadataRoundTrip`:
  - `test_create_and_retrieve_all_metadata_fields` — round-trip всех полей
  - `test_create_without_metadata_returns_fallback` — fallback без метаданных
  - `test_create_with_json_metadata_field` — JSON `metadata` → merge → preview
  - `test_patch_metadata_then_retrieve` — PATCH → preview → verify
  - `test_patch_metadata_not_found` — 404 для несуществующего черновика
- [x] Полный прогон: **363 passed**
