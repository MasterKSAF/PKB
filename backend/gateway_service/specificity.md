# Specificity / Аномалии

## 2026-06-12: Добавлены эндпоинты `/classifiers/pending`

### Изменения
- `mocks/registry_service/main.py` — добавлены 3 псевдонима:
  - `GET /classifiers/pending` → `list_quarantine`
  - `POST /classifiers/pending/{id}/accept` → `accept_quarantine`
  - `POST /classifiers/pending/{id}/reject` → `reject_quarantine`
- `mocks/tests/test_api.py` — добавлены 3 теста (test_100b, test_100c, test_100d)
- `mocks/gateway.py` — добавлен `RequestLogMiddleware` (логгирует все >>> запросы и <<< ответы)
- `mocks/auth_service/main.py` — логгирование в `create_role` (тело запроса)
- `mocks/registry_service/main.py` — логгирование в `list_pending/accept_pending/reject_pending`
- `mocks/orchestrator_service/main.py` — логгирование в `_get_document/search_get/list_drafts/create_draft`

### Аномалии
1. **Checker шлёт JSON на `POST /drafts/`** — эндпоинт ожидает `multipart/form-data` (файл). Не ошибка mock, checker должен слать форму.
2. **Checker не передаёт `q` в `GET /documents/search`** — параметр обязательный по спецификации, mock валидирует корректно.
3. **Checker registry-doc_id (int) суёт в orchestrator** — 12 эндпоинтов получают 422. Ошибка prepare-шагов checker'а.
4. **Checker не передаёт `document_key` в `GET /drafts/`** — параметр обязательный, mock валидирует.
5. **POST /admin/roles** — checker шлёт невалидный JSON (возможно camelCase поля). Mock ожидает `{"name": str, "permissions": List[str]}`.
