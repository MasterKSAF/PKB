# План: Уточнение схемы данных и API для связей task↔draft↔document

## Цель
- **Данные черновиков (drafts)** — таблица в **Registry** (`registry.drafts`)
- **Управление пайплайном** — в **Orchestrator**, который вызывает Registry для data-операций
- **task** — агрегатор этапов пайплайна, хранит промежуточные данные от сервисов
- **document** ссылается на **draft** (`registry.documents.draft_id`), а не наоборот

---

## Порядок выполнения работ

### Шаг 1. Изменения в БД — `docs/database/db_diagrams.md`
- [x] 1.1. Перенос `pipeline.drafts` → `registry.drafts` (новые поля + убрать task_id FK)
- [x] 1.2. Добавить `pipeline.tasks` и `pipeline.task_steps`
- [x] 1.3. Добавить `draft_id` в `registry.documents`
- [x] 1.4. Обновить ER-диаграмму (связи)
- [x] 1.5. Добавить индексы

### Шаг 2. Изменения в API Registry — `docs/api/registry_service_api.md`
- [x] 2.1. Обновить описание сервиса Registry (добавить drafts)
- [x] 2.2. Добавить группу `drafts` (internal) с эндпоинтами
- [x] 2.3. Добавить коды ошибок для drafts

### Шаг 3. Изменения в API Orchestrator — `docs/api/orchestrator_service_api.md`
- [x] 3.1. Обновить описание Orchestrator (task_steps, вызов Registry)
- [x] 3.2. Обновить ответы эндпоинтов группы drafts (task_id, draft_id, document_id)
- [x] 3.3. Обновить `GET /tasks/{task_id}/status` (draft_id, document_id, steps)

### Шаг 4. Изменения в Gateway — `docs/api/gateway_service_api.md`
- [x] 4.1. Проверить и обновить маршрутизацию `/api/v1/drafts/*` → Orchestrator

### Шаг 5. Изменения в пайплайнах
- [x] 5.1. Sequence-диаграммы: `POST /drafts` → Orchestrator → task + `POST /registry/drafts`
- [x] 5.2. Sequence-диаграммы: `PATCH /drafts/{id}/decide` → Orchestrator → Registry
- [x] 5.3. FSM черновика — данные в Registry, управление через Orchestrator
- [x] 5.4. Матрица ответственности — Registry для данных черновиков, Orchestrator для pipeline

### Шаг 6. Изменения в общих документах
- [x] 6.1. `docs/README.md` — обновить описания Orchestrator и Registry
- [x] 6.2. `docs/glossary.md` — обновить draft, draft_id, task_id
- [x] 6.3. `docs/api/common_api.md` — обновить идентификаторы (draft_id → Registry, task_id → Orchestrator)
- [x] 6.4. `docs/specificity.md` — добавить запись в "История решений"

### Шаг 7. Финальная проверка
- [x] 7.1. Сверка с todo.md — все пункты выполнены
- [x] 7.2. Перепросмотр изменений — несоответствия исправлены
- [x] 7.3. Проверка целостности и связанности — OK
