# Todo — Status

## ✅ 1. Добавить `/classifiers/pending` эндпоинты в registry mock — DONE
- `GET /classifiers/pending` — аналог `/classifiers/quarantine`
- `POST /classifiers/pending/{id}/accept` — аналог `/classifiers/quarantine/{id}/accept`
- `POST /classifiers/pending/{id}/reject` — аналог `/classifiers/quarantine/{id}/reject`

**Файл:** `mocks/registry_service/main.py` (добавлены псевдонимы)
**Тесты:** `mocks/tests/test_api.py` (test_100b, test_100c, test_100d)

## ✅ 2. POST /admin/roles (422) — расследование DONE

Mock ожидает: `{"name": str, "permissions": List[str]}` (модель `CreateRoleRequest`).
- Существующий тест `test_17_create_role` проходит (201)
- Причина 422 — checker шлёт невалидный JSON (не те поля), это не проблема mock
- Добавлен `logger.info` в `create_role` — при запуске checker'а будет видно тело запроса

## ✅ 3. GET /documents/search — проверка query params DONE

Mock уже имеет `q: str = Query(...)` с обязательным параметром (422 при отсутствии).
- Существующие тесты `test_36_post_search`, `test_37_get_search`, `test_38_search_with_filters` проходят
- Проблема в checker'е — он не шлёт `q`

## ✅ 4. Добавлено логгирование в mock-сервисы — DONE

- `mocks/gateway.py` — `RequestLogMiddleware` (логгирует все запросы >>> и ответы <<<)
- `mocks/auth_service/main.py` — `create_role` (тело запроса)
- `mocks/registry_service/main.py` — `list_pending`, `accept_pending`, `reject_pending`
- `mocks/orchestrator_service/main.py` — `_get_document`, `search_get`, `list_drafts`, `create_draft`

## ❌ Не фиксится в mock (проблемы checker'а)
- **12 документных 422** — checker registry-doc_id суёт в orchestrator
- **GET /drafts/** — checker не шлёт `document_key`
- **POST /drafts/** — checker шлёт JSON вместо multipart/form-data с файлом
