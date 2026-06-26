# Исправление падающих тестов (6 шт.)

## Причина
- `get_draft` / `get_draft_preview` не замоканы → корутина вместо dict
- `test_decide_wrong_stage` проверял неактуальное поведение (upload теперь разрешён)
- `TestApproveDraftMetadataOverrides` проверял несуществующий ключ `metadata_overrides` (код делает `update`)

## Исправлено
- [x] 1. `test_pipeline_formation.py` — добавлены моки get_draft / get_draft_preview в 5 тестов
- [x] 2. `test_drafts.py` — исправлен test_decide_wrong_stage: `upload` → `full`
- [x] 3. `test_pipeline_formation.py` — исправлен metadata_overrides: проверка `title`/`doc_code` вместо `metadata_overrides`
- [x] 4. 321 passed, 0 failed
