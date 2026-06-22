# Устранение всех фиксированных ID

## Принцип
Каждый ID должен либо динамически создаваться через pre-prepare, либо получаться из ответа предыдущего шага. Хардкодные ID удаляются.

## 1. `draft_id` — fallback в API Coverage
- [x] заменён на Gateway draft creation (retry + raise)

## 2. `task_id` — был хардкор 12345
- [x] добавлен pre-prepare Gateway draft → `task_id` для converter/parser/ocr
- [x] `{task_id}` резолвится из контекста, как и остальные ID

## 3. `draft_id`, `version_id`, `doc_id` — хардкоры в service defs
- [x] все заменены на `{variable}` с источниками в контексте

## 4. `base_data` — Gateway и Orchestrator
- [x] очищен до `{}`

## 5. `section_id` — API Coverage
- [x] динамический timestamp-based

## 6. Pipeline definitions
- [x] `draft_id`, `section_id`, `version_id` — payload-значения (не FK), оставлены литералами

## 7. Проверка
- [x] Все тесты — **537 passed**
- [x] `specificity.md` — запись #48
