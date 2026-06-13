# План: научить coverage test подставлять ID для раздельного тестирования API

## Проблема
Coverage test для Orchestrator: 22/30 skipped. Контекст (draft_id, task_id, doc_id, access_token) не подставляется, т.к.:
1. `test_service()` очищает контекст перед каждым сервисом — токен auth не наследуется
2. У оркестратора нет prepare_endpoints — неоткуда взять draft_id, task_id
3. Для doc_id нет создающего эндпоинта в оркестраторе
4. `needs_auth=True`, но получить JWT негде (prepare идут на порт сервиса, а auth на 8082)

## Решение

### [ ] 1. EndpointDef — добавить `override_port` (для prepare на других портах)
**Файл:** `services/base.py`
- Добавить `override_port: Optional[int] = None` в EndpointDef
- Если указан — `_execute_endpoint` использует его вместо port сервиса

### [ ] 2. coverage test — поддержка override_port
**Файл:** `api_coverage_test.py`
- В `_execute_endpoint`: если `ep.override_port` не None → `target_port = ep.override_port`
- В `test_service`: при вызове prepare передавать порт с учётом override_port

### [ ] 3. Orchestrator — добавить prepare_endpoints + base_data
**Файл:** `services/orchestrator.py`
- Prepare 1: GET /api/v1/auth/token (через override_port=8082) → access_token
- Prepare 2: POST /api/v1/drafts/ → draft_id, task_id
- Для doc_id: base_data = {"doc_id": 1} + expected_status={200, 202, 404} на документных эндпоинтах
- Для search и tasks — expected_status где нужно

### [ ] 4. Проверить результат
- `python -m service_checker docker --action coverage`
- Orchestrator: passed >= 20/30, skipped <= 10
