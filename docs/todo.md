# Todo — синхронизация preview-метаданных

> 18.06.2026 — поля preview-метаданных приведены к табличным именам.

- [x] **1.** `docs/schema/schema_converter_preview.json` — эталонная JSON-схема ✅
- [x] **2.** `docs/api/converter_validator_service_api.md` — Preview API ✅
- [x] **3.** `docs/api/orchestrator_service_api.md` — 5 примеров `preview_metadata` ✅
- [x] **4.** `docs/api/registry_service_api.md` — 4 примера `preview_metadata` ✅
- [x] **5.** `docs/pipelines/pipeline1-formation.md` — пример preview-метаданных ✅
- [ ] **6.** `docs/pipelines/pipeline1-formation_detail.md` — нет примера JSON, пропущено
- [x] **7.** `docs/specifications/converter_specification.md` — шаг 3, режимы ✅
- [x] **8.** `docs/database/db_diagrams.md` — §0 описание `preview_metadata` ✅
- [x] **9.** `docs/README.md` — чейнджлог ✅
- [x] **10.** Перепроверка ✅

---

## Этап 2: preview-слепок сохраняется

- [x] **1.** `docs/database/db_diagrams.md` — добавлен `preview_snapshot` в ER + примечания §0, §1 ✅
- [x] **2.** `docs/pipelines/pipeline1-formation.md` — шаг 3.0 (копирование preview) ✅
- [x] **3.** `docs/specifications/converter_specification.md` — принцип «Preview-метаданные сохраняются» ✅
- [x] **4.** `docs/api/registry_service_api.md` — `preview_snapshot` в примере ответа GET /documents/{id} + описание в ключевых полях ✅
- [x] **5.** `docs/database/ddl_migrations_17_06.md` — переписан в описательный стиль (без SQL), добавлен `preview_snapshot` ✅
- [x] **6.** `docs/README.md` — чейнджлог + обновлено описание ddl_migrations ✅
