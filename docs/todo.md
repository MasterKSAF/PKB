# Todo: Унификация health-эндпоинта Orchestrator + перенос monitor/metrics в Gateway

## Задача
1. ✅ `/api/v1/monitor/health` → `/api/v1/health` (выполнено)
2. ✅ `GET /api/v1/monitor/metrics` — перенесён из Orchestrator в Gateway как собственный endpoint

## Результат

### 1. ✅ `api/gateway_service_api.md`
- Удалена строка `/api/v1/monitor/metrics` из таблицы маршрутизации
- Добавлена строка в таблицу собственных эндпоинтов Gateway
- Добавлена полная спецификация `GET /api/v1/monitor/metrics`

### 2. ✅ `api/orchestrator_service_api.md`
- Удалён `GET /monitor/metrics` и его спецификация
- Группа `monitor` заменена на `health` в таблице групп
- Заголовок группы `health` убран (один эндпоинт)

### 3. ✅ `api/common_api.md`
- Таблица эндпоинтов: добавлен Gateway entry для `/api/v1/monitor/metrics`
- RBAC: `GET /monitor/metrics` — остаётся (теперь Gateway endpoint)
- Rate limiting: не требуется (попадает под "Остальные эндпоинты")

### 4. ✅ `README.md`
- Orchestrator: `/monitor/*` → `/health`
- Gateway: добавлена строка про метрики `/api/v1/monitor/metrics`

### 5. ✅ `specificity.md`
- Дополнена запись о переносе monitor/metrics в Gateway
