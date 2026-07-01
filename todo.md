# Todo — Исправление загрузки документов (завершено 01.07)

### Выполнено
- [x] **Upsert в `create_pipeline_document`** — при `payload.document_id` обновляет существующий документ (поля + sections + terminology + references), а не создаёт новый
- [x] **Нормализация ответа в `RegistryServiceClient.create_document`** — реальный Registry возвращает без обёртки `data`; клиент оборачивает, чтобы `current_doc_id` корректно обновлялся
- [x] **Нормализация ответа в `RegistryServiceClient.get_document_sections`** — аналогично
- [x] **`mock_response` для `get_document_sections`** — исправлен формат на без `data`
- [x] **Поддержка `sections` / `content` ключей** — `create_pipeline_document` читает `content` или `sections` из `document`
- [x] **Условное удаление старых sections** — удаляются только если есть новые на замену
- [x] **Тест `test_create_pipeline_document_upsert_existing`** — проверяет upsert через registry_service
- [x] **Исправлен `test_registry_sections.py`** — убрана ошибочная `data` обёртка при чтении sections
- [x] Все 125 тестов registry_service проходят
- [x] E2E тест **PASS**: pipeline completed, 76 sections в Registry, дублирования нет
