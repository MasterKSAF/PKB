# План тестирования Web-операций

## Структура документации

| Файл | Компонент | Тестов | Строк |
|------|-----------|--------|-------|
| [`01-gateway-service.md`](01-gateway-service.md) | Gateway Service (backend) | 16 файлов | ~1700 |
| [`02-orchestrator-service.md`](02-orchestrator-service.md) | Orchestrator Service (backend) | 6 файлов | ~950 |
| [`03-frontend-infra.md`](03-frontend-infra.md) | Frontend — инфраструктура тестов | — | — |
| [`04-frontend-api-mappers.md`](04-frontend-api-mappers.md) | Frontend — API mappers (http.ts) | 18 файлов | ~2650 |
| [`05-frontend-components.md`](05-frontend-components.md) | Frontend — React компоненты | 14 файлов | ~2840 |
| [`06-frontend-store.md`](06-frontend-store.md) | Frontend — Zustand store | 1 файл | ~200 |
| [`07-by-service.md`](07-by-service.md) | Распределение по backend-сервисам | — | — |

## Сводка

| Компонент | Файлов | Строк |
|-----------|--------|-------|
| Gateway Service | 16 | ~1700 |
| Orchestrator Service | 6 | ~950 |
| Frontend API mappers | 18 | ~2650 |
| Frontend Components | 14 | ~2840 |
| Frontend Store | 1 | ~200 |
| Инфраструктура | 3 | ~100 |
| **ИТОГО** | **58** | **~8440** |

## Приоритет по критичности

1. **Gateway Routing** (resolve_service + middleware) — основа всего Web — частично покрыто
2. **RBAC** — безопасность, не тестирована в реальном Gateway
3. **Frontend API (http.ts)** — все мэпперы ответов, обработка ошибок — не тестированы
4. **Frontend компоненты** — критичные: Login, Chat, Search, KnowledgeProcessing, DocumentRegistry
5. **Реальные эндпоинты Gateway** — health, diagnostics, metrics
6. **Gateway proxy_request** — проксирование к сервисам
