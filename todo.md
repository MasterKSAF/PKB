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

### [x] 3. Gateway — прокси path и query + fallback диагностика
  - [x] `gateway_diagnostics` — проксирует path и query на diagnostics server
  - [x] Fallback: если diagnostics server недоступен — gateway сам отдаёт базовую диагностику
  - [x] `_gateway_summary_diagnostics()` — конфиг + health сервисов
  - [x] `_gateway_service_diagnostics()` — health + URL конкретного сервиса
  - [x] Совместимость со старым DIAGNOSTICS_URL

### [ ] 4. Деплой и проверка
  - [ ] `git push`
  - [ ] На сервере: `git pull && docker compose up -d --build gateway`
  - [ ] Проверить `/api/v1/system/diagnostics`
