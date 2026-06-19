# Словарь данных (Data Dictionary)

> Матрица «термин/поле → где используется».
> При изменении поля — проверить все строки этой таблицы.

---

## Поля и их вхождения

| Поле / Термин | API-спеки | Пайплайны | БД | Спецификации |
|---|---|---|---|---|
| `preview_metadata` | orchestrator, registry, converter | pipeline1-formation (пример) | `registry.drafts.preview_metadata` | converter_specification |
| `title_hash_sha256` | orchestrator, registry, converter | pipeline1-formation (формула) | `registry.documents.title_hash_sha256` | normalizer_specification |
| `title_key` | orchestrator, registry, converter | pipeline1-formation (формула + пример preview) | `registry.documents.title_key` | normalizer_specification |
| `raw_data` | orchestrator (GET /drafts/{id}) | — | `registry.drafts.raw_data` | — |
| `notifications[]` | orchestrator (GET /drafts/{id}) | pipeline1-formation | `pipeline.draft_notifications` | — |
| `task.status` | orchestrator (GET /tasks/{id}/status) | overview (FSM P1+P2) | `pipeline.tasks.status` | — |
| `draft.status` | orchestrator (GET /drafts), registry | pipeline1-formation (FSM) | `registry.drafts.status` | — |
| `document.processing_status` | orchestrator (GET /documents/{id}) | pipeline2-indexation (FSM) | `registry.documents.processing_status` | — |
| `decided_by` | orchestrator (DecideResponse) | — | `registry.document_history` | — |
| `decided_at` | orchestrator (DecideResponse) | — | `registry.document_history` | — |
| `confidence` | orchestrator, registry, converter | pipeline1-formation | `registry.drafts.confidence` | converter_specification |
| `estimated_completion` | orchestrator (POST /drafts/{id}/preview, GET /documents/queue) | — | — | — |
| `valid_from` | orchestrator (PATCH /metadata, PATCH /decide), registry | — | `registry.documents.valid_from` | — |
| `valid_until` | orchestrator (PATCH /metadata, PATCH /decide), registry | — | `registry.documents.valid_until` | — |
| `source_type` | orchestrator, registry, converter, common | pipeline1-formation | `registry.documents.source_type` | converter_specification |
| `era` | orchestrator, registry, converter | pipeline1-formation | `registry.documents.era` | — |
| `jurisdiction` | orchestrator, registry, converter | — | `registry.documents.jurisdiction` | — |
| `issuing_body` | orchestrator, registry, converter | — | `registry.documents.issuing_body` | — |
| `mks_oks_code` | orchestrator, registry, converter | pipeline1-formation | `registry.documents.mks_oks_code` | converter_specification |
| `okstu_code` | orchestrator, registry, converter | pipeline1-formation | `registry.documents.okstu_code` | converter_specification |
| `udk_code` | orchestrator, registry, converter | pipeline1-formation | `registry.documents.udk_code` | — |
| `pkb_codes` | orchestrator, registry, converter | pipeline1-formation | (через categories) | pkb_domains |
| `document_type` | orchestrator, registry, converter | pipeline1-formation | `registry.documents.document_type` | — |
| `file_key` | orchestrator, registry | — | MinIO | — |
| `document_key` | orchestrator, registry | — | `registry.drafts.document_key` | — |
| `draft_id` | orchestrator, registry, gateway | pipeline1-formation | `registry.drafts.id` | — |
| `task_id` | orchestrator, gateway | overview | `pipeline.tasks.id` | — |
| `document_id` | orchestrator, registry, query | overview | `registry.documents.id` | — |
| `version_id` | orchestrator, registry | — | `registry.document_versions.id` | — |

---

## Статусные модели

| Модель | Где определена | Статусы |
|--------|---------------|---------|
| `task.status` | orchestrator_service_api.md | `uploaded`, `previewing`, `ready_for_approve`, `processing`, `created`, `indexing`, `indexed`, `failed` |
| `draft.status` | orchestrator_service_api.md, pipeline1-formation.md | `uploaded`, `previewing`, `ready_for_approve`, `review_required`, `validation`, `approved`, `discarded` |
| `document.processing_status` | pipeline2-indexation.md, db_diagrams.md | `pending_index`, `indexing`, `indexed`, `failed`, `partially_indexed` |

---

## Форматы health

| Тип | Путь | Формат | Где описан |
|-----|------|--------|-----------|
| Внутренние сервисы | `GET /api/v1/health` | `status`, `service`, `version`, `uptime_seconds` | common_api.md |
| Gateway (внешний) | `GET /api/v1/system/health` | `status`, `version`, `services{}`, `timestamp`, `endpoints_total` | gateway_service_api.md |
