# todo — перенос `POST /documents/{doc_id}/reprocess` из Orchestrator в Registry

## Задача
Эндпоинт `POST /documents/{doc_id}/reprocess` перенесён из Orchestrator Service в Registry Service. Документация приведена в соответствие.

## План
- [x] 1. **`orchestrator_service_api.md`** — удалён раздел `POST /documents/{doc_id}/reprocess`
- [x] 2. **`orchestrator_service_api.md`** — убрано упоминание reprocess в `GET /drafts/{draft_id}/tasks`
- [x] 3. **`orchestrator_service_api.md`** — убрана колонка `reprocess` из таблицы операций черновика
- [x] 4. **`orchestrator_service_api.md`** — убрано упоминание reprocess в `POST /drafts/{draft_id}/preview`
- [x] 5. **`registry_service_api.md`** — добавлен `POST /registry/documents/{doc_id}/reprocess` (3.13) + строка в таблицу методов
- [x] 6. **`common_api.md`** — ALREADY_PROCESSING помечен как Registry, Orchestrator; Edge Cases исправлен
- [x] 7. **`README.md`** — обновлена строка статуса UI-интеграции
- [x] 8. **`rag_builder_service_api.md`** — уточнена ссылка на Registry API
- [x] 9. **`pipelines/overview.md`** — FSM `failed → uploaded` помечен как reprocess (Registry)
- [x] 10. **`pipelines/pipeline1-formation.md`** — исправлены ссылки на Registry
- [x] 11. **`pipelines/pipeline2-indexation.md`** — исправлены ссылки на Registry
- [x] 12. **Финальная проверка целостности** — выполнена, оставшихся упоминаний в Orchestrator нет
