# Правки: todo_fix_docs_vs_code.md + проверка тестов

## Статус: ВЫПОЛНЕНО

## Приоритет 1 — Ошибки в кодах ответов
- [x] 1.1 UNSUPPORTED_FILE_TYPE → 422 (вместо 400)
- [x] 1.2 PREVIEW_ALREADY_RUNNING → PREVIEW_IN_PROGRESS
- [x] 1.3 TASK_ALREADY_TERMINAL → DRAFT_ALREADY_DECIDED

## Приоритет 2 — Недостающая валидация
- [x] 2.1 FILE_TOO_SMALL (< 1 КБ)
- [x] 2.2 DUPLICATE_FILE — блокировка при создании черновика
- [x] 2.3 Пороги качества (auto-approve) — config + _check_auto_approve

## Приоритет 3 — Новая функциональность
- [x] 3.1 confirm action — ALL_ACTIONS + confirm_draft + decide проверка
- [x] 3.2 DUPLICATE_FILE_AFTER_APPROVE — обработка в approve_draft
- [x] 3.3 BUSINESS_KEY_DRIFT — проверка в approve_draft
- [x] 3.4 Idempotency-Key для POST /preview

## Тесты
- [x] Запустить существующие тесты, проверить состояние
- [x] Обновить тесты под новые коды ошибок (7 файлов, 58+ изменений)
- [x] Финальный прогон: 543 passed, 3 failed (предсуществующие)
