# Завершено: path-pattern routing в Gateway

## Что сделано
- Замена префиксной маршрутизации `SERVICE_ROUTES` на `ROUTE_TABLE` с `RouteEntry` (path-pattern + HTTP-метод)
- `resolve_service(method, path)` → `(service_name, target_path)` — учитывает метод, возвращает целевой путь
- URL-трансформация для Registry: `/api/v1/documents/{id}` → `/api/v1/registry/documents/{id}`
- `proxy_request` принимает опциональный `target_path` для путей с трансформацией
- Обновлён `routers.py` — передаёт `method` в `resolve_service`, использует `target_path`
- 81 тест (было 14) — полное покрытие всех граничных случаев
- Актуализированы README.md, guide.md, specificity.md
