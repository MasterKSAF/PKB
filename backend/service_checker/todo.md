# Исправить Parser: создать черновик в Registry перед вызовом

## Проблема
Checker шлёт Parser'у `draft_id: 1` (хардкод), но в чистой БД Registry не содержит черновиков. Parser не может записать статус → 422.

## План
- [x] 1. `core/api_coverage_test.py` — pre-prepare для Parser: создать документ в Registry → draft_id
- [x] 2. `services/parser.py` — заменить хардкод `draft_id: 1` на `draft_id: "{draft_id}"`, mode=preview→full, убрать `preview_not_supported` из response_schema
- [x] 3. Проверка: Parser 5/5 — 0 failed

# Разные имена отчётов при фильтрации (--api/--pipeline)

## Проблема
При запуске `recheck.bat --api query,rag_builder` или `--pipeline chat_inference`
отчёты сохранялись с теми же именами `full_report.md`/`api_coverage.md`,
перетирая базовые отчёты полного прогона.

## Что сделано
- [x] `core/cli.py` — добавлен `report_suffix`, формируемый из `--services` и `--pipelines`
- [x] Имена файлов: `full_report{report_suffix}.md`, `api_coverage{report_suffix}.md`
- [x] Пример: `recheck.bat --api query,rag_builder` → `full_report_services_query_rag_builder.md`
- [x] Пример: `recheck.bat --pipeline chat_inference` → `full_report_pipelines_chat_inference.md`
- [x] Без фильтров — имена не меняются (обратная совместимость)
- [x] `core/cli.py` — нормализация `services`/`pipelines` (split по запятой) на входе в `cmd_docker`
- [x] Исправлено: `recheck.bat --api query,rag_builder` теперь правда тестирует query и rag_builder

# RAG Builder 500: FK fk_rag_document_chunks_section_id

## Проблема
`rag.document_chunks` имеет FK `fk_rag_document_chunks_section_id` → `registry.document_sections(id)`.
Checker шлёт `section_id: 1`, но в БД нет секции → FK violation → 500.
Миграция на удаление FK не накачена.

## Что сделано
- [x] `core/api_coverage_test.py` — pre-prepare RAG Builder: `ALTER TABLE ... DROP CONSTRAINT IF EXISTS fk_rag_document_chunks_section_id`
- [x] `pipelines/base.py` — `PipelineRunner.run()`: то же самое перед пайплайнами с RAG Builder
- [x] Проверка: RAG Build status=201, completed
