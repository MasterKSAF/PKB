# todo — перенос поисковых эндпоинтов из Query → Registry

## Задача
- `POST /documents/search`, `GET /documents/search` — перенесены из Query Service в Registry Service
- `POST /ask` — удалён из Query Service

## План
- [x] 1. **`query_service_api.md`** — удалена группа search (`POST /documents/search`, `GET /documents/search`, `POST /ask`)
- [x] 2. **`registry_service_api.md`** — добавлен `POST /registry/documents/search` (3.1b); `GET /registry/documents/search` (3.1c) удалён из-за конфликта с BM25 (3.1a)
- [x] 3. **`gateway_service_api.md`** — убраны `/api/v1/search/*` и `/api/v1/ask` из routing table
- [x] 4. **`common_api.md`** — добавлена строка RBAC для `POST /registry/documents/search`
- [x] 5. **`README.md`** — обновлены описания Query Service и Registry Service
- [x] 6. **Финальная проверка целостности** — выполнена, оставшихся упоминаний нет
