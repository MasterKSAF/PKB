# Todo

## 1. Registry не имеет эндпоинта POST /registry/drafts

> Создан: 22.06.2026
> Статус: ✅ Выполнено

### Проблема
`RegistryServiceClient.create_draft()` вызывает `POST /registry/drafts` на registry-service,
но registry-service **не имеет** этого эндпоинта. Эндпоинт есть только в mock-клиенте
оркестратора (`_generate_mock`). При `REGISTRY_SERVICE_MOCK=false` клиент делал
реальный HTTP-запрос и получал 404.

### Сделано
- [x] Добавлен fallback в `RegistryServiceClient.call()` — при 404 на `/registry/drafts*`
      клиент переключается на in-memory mock с логом предупреждения
- [x] Document-эндпоинты (`/registry/documents/*`) не затронуты
- [x] Зафиксировано в `specificity.md` (п. 2.6)
- [x] 304 тестов проходят

### Что остаётся
- Registry service должен реализовать группу `/registry/drafts`

---

## 2. Восстановление POST /documents/{doc_id}/reprocess

> Создан: 22.06.2026
> Статус: ✅ Выполнено

### Проблема
Коммит `a739338` удалил `POST /documents/{doc_id}/reprocess` из оркестратора,
но это pipeline-операция (P2I-9), требующая управления Celery-задачей.
Оркестратор управляет индексацией и целостностью документов — reprocess должен быть здесь.

### Сделано
- [x] Восстановлен `app/schemas/documents.py` — ReprocessMode, ReprocessRequest, ReprocessResponse
- [x] Восстановлен `app/api/v1/endpoints/documents.py` — POST /{doc_id}/reprocess
- [x] Восстановлен `app/tasks/pipeline_indexation.py` — run_reprocess_step Celery task
- [x] Обновлён `app/api/v1/api.py` — подключен documents router
- [x] Обновлён `app/models/pipeline.py` — pipeline_type включает "reprocess"
- [x] Обновлён `specificity.md` (п. 2.5)
- [x] Восстановлен `tests/test_documents_api.py` — 5 тестов TestDocumentReprocess
- [x] Восстановлена проверка в `tests/test_health.py` — `/api/v1/documents/{doc_id}/reprocess` в OpenAPI
- [x] 309 тестов проходят (было 304 + 5 reprocess)

### Не восстановлено
- `tests/test_pipelines.py` — импортирует типы, удалённые из `app/schemas/documents.py`
  (DocumentStatusProcessing, FormationPipeline, ChunkSummary и др.), которые относились
  к GET /documents/* и были перенесены в registry-service. Восстановление файла
  потребовало бы восстановления всей старой схемы документов, что противоречит архитектуре.
