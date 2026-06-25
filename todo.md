# Diagnostics: расширение endpoint

## Цель
Разделить diagnostics на уровни:
- базовая сводка (`/diagnostics`)
- детальная по сервису (`/diagnostics/gateway`, `/diagnostics/parser`, ...)
- расширенная (`?verbose=true&logs=100`)

## План

### [x] 1. `server_diagnostics.sh` — рефакторинг
  - [x] Выделены функции-блоки: `system_info()`, `disk_usage()`, `git_status()`, ...
  - [x] Флаги: `--summary`, `--service <name>`, `--verbose`, `--logs <N>`
  - [x] `service_diagnostics()` — inspect + health + stats + logs по контейнеру
  - [x] `system_logs()` — dmesg, journalctl, memory pressure, CPU load

### [x] 2. `diagnostics_server.py` — расширение
  - [x] Парсинг path для роутинга: `/diagnostics` → summary, `/diagnostics/{service}` → по сервису
  - [x] Парсинг query params: `verbose`, `logs`
  - [x] `/diagnostics/system` → системные логи
  - [x] Валидация известных сервисов (404 для неизвестных)

### [x] 3. Gateway — прокси path и query
  - [x] `gateway_diagnostics` — `@app.get("/api/v1/system/diagnostics/{rest_of_path:path}")`
  - [x] Проброс query string на diagnostics server
  - [x] Совместимость со старым DIAGNOSTICS_URL (с /diagnostics на конце)

### [ ] 4. Проверка на сервере
  - [ ] deploy.sh → перезапуск gateway + diagnostics server (перезапустить diagnostics)
  - [ ] `curl /api/v1/system/diagnostics` — базовая сводка
  - [ ] `curl /api/v1/system/diagnostics/gateway` — по сервису
  - [ ] `curl /api/v1/system/diagnostics/system` — системные логи
  - [ ] `curl "/api/v1/system/diagnostics?verbose=true&logs=10"` — проверка params
