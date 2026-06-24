# План исправления Orchestrator API — ЗАВЕРШЕНО

## Статус (2026-06-23, финал)

**Pipeline**: 15 пайплайнов — ✅ **15 пройдено**, ❌ **0 падают**
**Unit-тесты**: 320 passed

## Что сделано

| Пункт | Проблема | Исправление |
|---|---|---|
| P0.1 | `GET /tasks/{task_id}/status` → 404 | Алиас в `tasks.py` |
| P0.2 | `GET /drafts/{draft_id}` → 405 | Прокси в Registry + трансформация ответа |
| P0.3 | `PATCH /drafts/{draft_id}/decide` → 409/500 | Разрешены стадии upload/preview; сбор метаданных; парсинг version_id |
| P0.4 | `PATCH /drafts/{draft_id}/metadata` → 404 | Метод в client + прокси |
| OR-14 | `{task_id_2}` не подставлялся | alt_map в чекере |
| preview_snapshot | Поле не найдено | check сделан optional |
