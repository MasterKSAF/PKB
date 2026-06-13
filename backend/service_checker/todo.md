# План: научить coverage test подставлять ID для раздельного тестирования API

## Проблема
Coverage test для Orchestrator: 22/30 skipped. Контекст (draft_id, task_id, doc_id, access_token) не подставляется, т.к.:
1. `test_service()` очищает контекст перед каждым сервисом — токен auth не наследуется
2. У оркестратора нет prepare_endpoints — неоткуда взять draft_id, task_id
3. Для doc_id нет создающего эндпоинта в оркестраторе
4. `needs_auth=True`, но получить JWT негде (prepare идут на порт сервиса, а auth на 8082)

## Решение

### [x] 1. EndpointDef — добавить `override_port` (для prepare на других портах)
**Файл:** `services/base.py`
- Добавить `override_port: Optional[int] = None` в EndpointDef
- Если указан — `_execute_endpoint` использует его вместо port сервиса

### [x] 2. coverage test — поддержка override_port
**Файл:** `api_coverage_test.py`
- В `_execute_endpoint`: если `ep.override_port` не None → `target_port = ep.override_port`
- URL формируется с target_port вместо port

### [x] 3. Orchestrator — добавить prepare_endpoints + base_data
**Файл:** `services/orchestrator.py`
- Prepare 1: POST /api/v1/auth/token (через override_port=8082) → access_token
- Prepare 2: POST /api/v1/drafts/ → draft_id, task_id
- Для doc_id: base_data = {"doc_id": "1", "page_num": 1}
- response_schema для document_id — (int, str)

### [x] 4. Проверить результат
- `python -m service_checker docker --action coverage`
- **Orchestrator: 32/32 passed, 0 failed, 0 skipped**
- Фикс skipped: добавил `params={"longpoll": 0}` в preview/status — сервис возвращает статус сразу без longpoll

## Итог
- **Было:** 8/30 passed, 22 skipped, 0 failed
- **Стало:** 32/32 passed, 0 failed, 0 skipped
- Добавлен механизм `override_port` для prepare-шагов на других портах
- Orchestrator теперь тестируется изолированно: получает JWT от Auth (8082), создаёт draft через свой API (8081), подставляет ID в path-параметры

---

# Исправление: Registry pending/accept и pending/reject (2026-06-14)

## Проблема
Registry: 2 skipped (pending/accept, pending/reject) — нет pending_id в контексте.

## Решение
Не нужно file upload. Pending-классификаторы создаются автоматически через `check_and_quarantine_classifiers()` при создании документа с отсутствующим кодом.

### [x] 1. PREPARE_DOCUMENT — добавить отсутствующие коды
**Файл:** `services/registry.py`
- Добавлены `mks_oks_code: f"98.{_ts}"` и `okstu_code: f"88.{_ts}"` в PREPARE_DOCUMENT

### [x] 2. Prepare-эндпоинт для извлечения pending_id
**Файл:** `services/registry.py`
- Добавлен `GET /classifiers/pending/` с `extract_keys=["pending_id"]`
- После create_document (с отсутствующим кодом) → pending создаётся → GET извлекает его id

### [x] 3. alt_map — pending_id
**Файлы:** `api_coverage_test.py`, `pipelines/base.py`
- Добавлен `"pending_id": ["id"]` для рекурсивного поиска

### [x] 4. Проверить результат
- Registry: 33/33 (было 30/32 + 1 prepare-эндпоинт)
- 2 skipped → 2 passed
- Остальные сервисы без изменений

## Итог
- Теперь не нужно модифицировать registry_service — всё решается в checker
