# Задачи (выполнено)

## 1. Анализ проблемы: черновики в "uploaded" без парсинга
- [x] Проанализирован код approve_draft, FULL_PHASE_MODE, dispatching
- [x] Root cause зафиксирован в specificity.md (раздел Pipeline)

## 2. Pre-existing падения (6 тестов)
- [x] Проверено: `OCR_ENABLED` и `PARSER_FALLBACK_TO_OCR` не найдены в docker-compose или .env
- [x] Во всех проверенных docker-compose файлах и .env этих переменных нет → defaults (True)
- [x] Тесты `test_config.py` проверяют defaults (ожидают True) — должны проходить

## 3. Покрыть decide_draft endpoint
- [x] Добавлены HTTP-тесты (TestClient) для:
  - `confirm` action (valid stage → 200 + status=validation, invalid stage → 409)
  - `BUSINESS_KEY_DRIFT` → 409
  - `DUPLICATE_FILE_AFTER_APPROVE` → 409 + conflict_document_id
- [x] Файл: `tests/orchestrator/test_decide_edge_cases.py`

## 4. FULL_PHASE_MODE="full" — защита
- [x] Добавлен warning-log в `approve_draft` orchestrator.py
  - Логирует предупреждение при `full` mode + `full_completed=False`
  - Указывает draft_id, task_id, рекомендует `auto` или `partial`
