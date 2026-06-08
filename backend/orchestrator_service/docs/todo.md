# План: Схлопывание `/parser/preview` и `/parser/process` в единый эндпоинт

## Цель
Объединить `POST /parser/preview` и `POST /parser/process` в единый эндпоинт с полем `mode`. Если движок не поддерживает постраничный парсинг — full с отметкой `preview_not_supported: true`. Auto-approve только при успешном извлечении метаданных и отсутствии дубликатов.

---

## Выполнено

### Изменённые файлы
- `docs/api/parser_service_api.md` — схлопнут preview в process, добавлены `mode`, `max_pages`, `preview_not_supported`
- `docs/api/ocr_service_api.md` — зеркальное изменение
- `docs/schema/schema_converter_preview.json` (бывш. schema_parser_preview) — добавлены `mode`, `preview_not_supported`
- `docs/specifications/parsing_specifications.md` — обновлён контракт preview
- `docs/pipelines/pipeline1-formation.md` — sequence-диаграмма, таблица шагов, параметры
- `docs/pipelines/pipeline1-formation_detail.md` — секция режимов работы
- `docs/pipelines/overview.md` — flowchart, таблицы, data flow
- `docs/api/orchestrator_service_api.md` — input_data в step preview_ocr
- `docs/README.md` — описание Parser Service
- `docs/specificity.md` — закрыты LP-C1, PL-E3, добавлена запись решения
