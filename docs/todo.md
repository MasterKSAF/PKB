# Todo: исправление auto-approve при preview_not_supported

**Проблема:** В документации多处 написано, что при `preview_not_supported=true` происходит auto-approve. Это некорректно. При `preview_not_supported` просто возвращается полный JSON (вместо частичного), full-фаза OCR/Parser пропускается, но все остальные стадии (Converter-validator preview, проверка уникальности, решение пользователя) выполняются обычно.

- [x] 1. `docs/6.dev_tasks_17_06.md` — PS-6: убрать "auto-approve при preview_not_supported"
- [x] 2. `docs/6.dev_tasks_17_06.md` — P1F-6: "Auto-approve при preview_not_supported" → "Пропуск full-фазы при preview_not_supported"
- [x] 3. `docs/api/parser_service_api.md` — строка 56: убрать упоминание auto-approve
- [x] 4. `docs/api/parser_service_api.md` — строка 114: убрать упоминание auto-approve
- [x] 5. `docs/api/ocr_service_api.md` — строка 56: убрать упоминание auto-approve
- [x] 6. `docs/api/ocr_service_api.md` — строка 112: убрать упоминание auto-approve
- [x] 7. `docs/pipelines/pipeline1-formation.md` — строка 162 (P.6a): убрать auto-approve
- [x] 8. `docs/pipelines/pipeline1-formation.md` — строка 170: убрать auto-approve из описания `preview_not_supported_fallback`
- [x] 9. `docs/pipelines/pipeline1-formation.md` — строка 161 (P.6): убрать "(или auto-approve)" из описания шага
- [x] 10. `docs/pipelines/pipeline1-formation.md` — строка 68: исправить "решение об auto-approve" на "full-фаза будет пропущена"
- [x] 11. `docs/specificity.md` — LP-C1: убрать auto-approve
- [x] 12. `docs/specificity.md` — раздел "Схлопывание preview/process": убрать auto-approve
- [x] 13. `docs/pipelines/pipeline1-formation_detail.md` — строки 225-227: убрать auto-approve
- [x] 14. Финальная проверка целостности и связности — пройдена
