# todo — фикс 7 противоречий в документации

## Источник
Анализ пользователя: 7 несоответствий в документации API и FSM.

## План правок

### P1. `review_required` — `decide` vs `operator-confirm`
- [x] 1.1. `pipeline1-formation.md` — заменить `PATCH /drafts/{draft_id}/operator-confirm` на `PATCH /drafts/{draft_id}/decide` с `action: "confirm"`
- [x] 1.2. `pipeline1-formation.md` — добавить `confirm` в описание FSM-перехода `review_required → validation`
- [x] 1.3. `orchestrator_service_api.md` — PATCH /decide: добавить действие `confirm` (review_required → validation) в таблицу и тела ответов

### P2. `metadata_overrides` — нет в публичном API Gateway
- [x] 2.1. `orchestrator_service_api.md` — PATCH /decide: добавить `metadata_overrides` как опциональное поле запроса
- [x] 2.2. `gateway_service_api.md` — PATCH /decide: упомянуть `metadata_overrides` в маршрутизации

### P3. `notifications[]` vs `issues[]` — расхождение
- [x] 3.1. `pipeline1-formation.md` — заменить `issues[]` на `notifications[]` в описании статуса `review_required`

### P4. `validation` статус отсутствует в enum статусов draft API
- [x] 4.1. `orchestrator_service_api.md` — GET /drafts: добавить `validation` и `review_required` в описание поля `status`
- [x] 4.2. `orchestrator_service_api.md` — GET /drafts filter: добавить `validation` в список статусов

### P5. `valid_from` / `valid_until` — неясность draft vs Registry
- [x] 5.1. `orchestrator_service_api.md` — добавить примечание к GET /drafts/{id}, что `valid_from`/`valid_until` появляются только в Registry после approve

### P6. `source_type` enum — RMRS расходится
- [x] 6.1. `registry_service_api.md` — /enums: добавить `RMRS` в `source_type`
- [x] 6.2. `db_diagrams.md` — примечание source_type: добавить `RMRS`
- [x] 6.3. `registry_service_api.md` — statistics: добавить `RMRS` в пример documents_by_source_type

### P7. `tasks/*` read-only контракт не подтверждён в Gateway
- [x] 7.1. `gateway_service_api.md` — добавить секцию маршрутизации `/api/v1/tasks/*` с описанием read-only эндпоинтов
- [x] 7.2. `gateway_service_api.md` — сноска в таблице маршрутизации ссылается на новую секцию
