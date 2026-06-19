# todo — правки по 9 стоперам (аудит 19.06)

## Источник
Анализ 9 стоперов, блокирующих UI-интеграцию.

---

### S1. Матрица actions по статусам + механизм оповещения
- [x] 1.1. `orchestrator_service_api.md` — PATCH /decide: добавить таблицу «Допустимые действия по статусам» (approve/reject/confirm для ready_for_approve, review_required и остальных)
- [x] 1.2. `orchestrator_service_api.md` — добавить описание механизма оповещения UI после `confirm → validation → approved` (pooling GET /drafts/{id})
- [x] 1.3. `orchestrator_service_api.md` — явно указать, что `metadata_overrides` игнорируется при `action: reject`

### S2. Статус validation в preview/status + терминальные статусы
- [x] 2.1. Отменено: `GET /drafts/{draft_id}/preview/status` возвращает статус preview-фазы (pending/processing/completed/failed), а не статус черновика. validation уже присутствует во всех перечислениях статусов черновика
- [x] 2.2. `orchestrator_service_api.md` — добавить таблицу «Терминальные и промежуточные статусы»
- [x] 2.3. `orchestrator_service_api.md` — добавить матрицу «Допустимые операции по статусам» (approve/reject/delete/reprocess)

### S3. Подтверждение notifications[]
- [x] 3.1. Подтверждено backend: публичное поле — `notifications[]`

### S4. Raw JSON editing — readonly
- [x] 4.1. Отложено до появления контракта. UI: readonly + copy/download

### S5. Отдельный endpoint для metadata_overrides
- [x] 5.1. `orchestrator_service_api.md` — добавить `PATCH /drafts/{draft_id}/metadata` с полной схемой запроса/ответа
- [x] 5.2. `orchestrator_service_api.md` — описать логику: пересчёт `title_hash_sha256` / `title_key` по правилам нормализатора
- [x] 5.3. `orchestrator_service_api.md` — описать повторную проверку уникальности при изменении ключевых полей
- [x] 5.4. `gateway_service_api.md` — добавить маршрут `/api/v1/drafts/{draft_id}/metadata` в routing table
- [x] 5.5. `gateway_service_api.md` — sequence diagram: добавить шаг редактирования метаданных до confirm
- [x] 5.6. `pipeline1-formation.md` — дополнить описание: metadata_overrides редактируются через PATCH /metadata до confirm

### S6. valid_from/valid_until в черновике
- [x] 6.1. `orchestrator_service_api.md` — обновить примечание: `valid_from`/`valid_until` возвращаются в `GET /drafts/{id}` если переданы через metadata_overrides
- [x] 6.2. `orchestrator_service_api.md` — PATCH /drafts/{draft_id}/metadata: включить valid_from/valid_until в редактируемые поля
- [x] 6.3. `orchestrator_service_api.md` — описать правило вывода valid_from по умолчанию из year (если не задан)

### S7. source_type enum — канонический
- [x] 7.1. Уже везде согласован, RMRS присутствует
- [x] 7.2. `specificity.md` — добавить рекомендацию UI: брать enum из `GET /registry/enums`

### S8. business key — главный ключ, DDL
- [x] 8.1. `db_diagrams.md` — явно указать, что главный бизнес-ключ: `title_hash_sha256`
- [x] 8.2. `db_diagrams.md` — пояснить `title_key` UNIQUE: технический (защита от коллизий не нужна для SHA-256, но индекс для быстрого аудита)
- [x] 8.3. `ddl_migrations_17_06.md` — дополнить: UNIQUE-индексы для `title_hash_sha256` и `title_key`
- [x] 8.4. `orchestrator_service_api.md` — PATCH /decide: добавить код ошибки `DUPLICATE_DOCUMENT` (409) при конфликте уникальности
- [x] 8.5. `gateway_service_api.md` — добавить `DUPLICATE_DOCUMENT` в таблицу ошибок

### S9. Consistency checker — фикс regex
- [x] 9.1. `check_consistency.py` — вынести набор префиксов task-ID в константу `TASK_PREFIXES`
- [x] 9.2. `check_consistency.py` — использовать единую константу в `get_task_ids()` и в проверке ссылок
