# План тестирования Orchestrator Service — РЕЗУЛЬТАТЫ

## Анализ покрытия

**Существующие тесты (до работы):**
- `test_health.py` — root, health check, OpenAPI
- `test_monitor.py` — metrics, auth mock behaviour
- `test_documents.py` — upload, list, get, status, delete, reprocess, errors, pages, parameters, queue, file
- `test_search.py` — POST/GET search, Ask endpoint
- `test_validate.py` — compare, get result, batch compare, checks, export
- `test_pipelines.py` — FSM enums, pipeline response structures, indexation, preview/decision FSM, approve, reprocess, delete, history, queue, edge cases
- `test_new_features.py` — task preview, preview status, decide, versions, approve, history, search validation, upload fields, list filters

**Новые тесты (созданы) — 12 файлов:**

| Файл | Сущность | Кол-во тестов |
|------|----------|:----------:|
| `test_base_client.py` | ServiceClient (dual-mode, HTTP клиент, ServiceError) | 19 |
| `test_config.py` | Settings, ServiceConfig, env vars | 13 |
| `test_error_handling.py` | APIException, ErrorResponse, endpoint error format | 21 |
| `test_service_clients_auth.py` | AuthServiceClient (token, users, roles, audit) | 19 |
| `test_service_clients_rag.py` | RAGServiceClient (index, search, generate) | 13 |
| `test_service_clients_query.py` | QueryServiceClient (text, sessions, messages, feedback) | 18 |
| `test_service_clients_validation.py` | ValidationServiceClient (extract, compare, check, calc, recommend) | 18 |
| `test_service_clients_ocr.py` | OCRServiceClient (process, engines) | 10 |
| `test_service_clients_integration.py` | IntegrationServiceClient (files, meridian, external) | 12 |
| `test_service_clients_registry.py` | RegistryServiceClient (classifiers, terms, docs, stats) | 29 |
| ~~`test_auth_real_mode.py`~~ | **Удалён** — авторизация вынесена на nginx | — |
| `test_integration_scenarios.py` | End-to-end Pipeline 1→2→3, Validation, Versions | 14 |

## Итоги

**Всего тестов:** 525 passed, 0 skipped
**Новых тестов написано:** ~186 в 11 новых файлах

**Пробелы до работы:**
1. ❌ → ✅ Unit-тесты Service Client'ов (7 клиентов, ~120 тестов)
2. ❌ → ✅ `ServiceError` / `APIException` / error response format
3. ❌ → ✅ `base_client.py` (dual-mode, HTTP, ошибки)
4. ❌ → ✅ `config.py` (env vars, defaults)
5. ❌ → ✅ Cross-pipeline интеграционные сценарии (14 сквозных тестов)
6. ❌ → ✅ Real auth mode — **не актуален**, авторизация вынесена на nginx
7. ❌ → ✅ RegistryClient (классификаторы, терминология, реестр)
8. ❌ → ✅ ValidationClient (extract, calculate, recommend)
9. ❌ → ✅ OCRClient, IntegrationClient
10. ❌ → ✅ QueryClient (сессии, чаты, фидбек)
11. ❌ → ✅ AuthClient (users CRUD, roles, audit)
12. ❌ → ✅ RAGClient (index, delete, generate)

## Архитектурное решение

Авторизация полностью вынесена из Orchestrator Service на nginx.
Все эндпоинты оркестратора — публичные.
Внутренний `Depends(get_current_user)` в mock-режиме всегда возвращает MOCK_USER.
При переходе на реальные сервисы безопасность обеспечивается на уровне nginx.
