# Этап 8. Упрощение статусной модели — ВЫПОЛНЕНО

## Статусы черновиков (drafts)
- ✅ `uploaded`, `previewing`, `ready_for_approve`, `approved`, `discarded`
- ✅ `draft` (FSM) → `uploaded`
- ✅ `new` (Draft FSM) → `uploaded`
- ✅ `promoted` (Draft FSM) → `approved`
- ✅ `preview_ready` (Draft FSM) → `ready_for_approve`

## Статусы документов (Registry)
- ✅ `created` (бывший `registry`), `pending_index`, `indexing`, `indexed`, `failed`
- ✅ Удалены: `draft`, `uploaded`, `previewing`, `awaiting_decision`, `parsing`, `validation`, `ready_for_promotion`, `review_required`, `approved`, `duplicate`, `new_version`, `archived`

## Файлы
- ✅ `docs/pipelines/pipeline1-formation.md` — FSM, таблицы, таймауты, компенсации
- ✅ `docs/pipelines/pipeline1-formation_detail.md` — терминальные статусы
- ✅ `docs/pipelines/overview.md` — сводная FSM, таблица, e2e, ключевые решения
- ✅ `docs/pipelines/pipeline2-indexation.md` — триггер `created`, таймауты
- ✅ `docs/api/registry_service_api.md` — document_status, статистика, модель
- ✅ `docs/api/orchestrator_service_api.md` — статусы черновиков и документов
- ✅ `docs/api/common_api.md` — обзор конвейера, идентификаторы
- ✅ `docs/api/converter_validator_service_api.md` — `review_required` → `manual`
- ✅ `docs/database/db_diagrams.md` — pipeline.drafts, registry.documents
- ✅ `docs/glossary.md` — таблицы статусов (черновики + документы)
- ✅ `docs/specificity.md` — API-B4, LP-C4, X4, LP-V1, LP-V2 обновлены
- ✅ `docs/README.md` — Draft FSM, статус документов
