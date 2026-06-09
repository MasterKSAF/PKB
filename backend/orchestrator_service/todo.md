# Retry (tenacity) + Circuit Breaker + Trace ID — ВЫПОЛНЕНО

## Что сделано

### 1. Trace ID — сквозная трассировка запросов ✅
- **`app/core/trace.py`** — contextvar `_trace_id`, функции `get_trace_id()`, `set_trace_id()`, `reset_trace_id()`, класс `TraceIdFilter`
- **`app/main.py`** — `trace_middleware`: читает `X-Trace-ID`/`X-Request-ID` из заголовка, генерирует UUID, возвращает в ответе
- **`app/core/logging_config.py`** — `TraceIdFilter` добавлен во все хендлеры, формат лога: `%(trace_id)-16s`
- **`app/models/pipeline.py`** — в модель `Task` добавлено поле `trace_id: String(32)`
- **`orchestrator.py`** — trace_id сохраняется в Task при старте, восстанавливается в `on_step_completed`, `on_step_failed`, `approve_draft`, `reject_draft`
- **`pipeline_formation.py`** — во все Celery задачи добавлен параметр `trace_id`, устанавливается в контекст при старте
- **Клиенты сервисов** — все вызовы через `base_client.py` логируются с trace_id

### 2. Retry через tenacity ✅
- **`base_client.py`** — в `_request_with_retry()` применяется `@tenacity.retry`:
  - `stop=stop_after_attempt(max_retries+1)`
  - `wait=wait_exponential(multiplier=2, min=1, max=60)`
  - Ретраит: `TimeoutException` и `HTTPStatusError` (5xx)
  - Не ретраит: `ConnectError`, 4xx
- Настройки: `MAX_RETRIES`, `RETRY_BACKOFF_FACTOR` из `HTTPClientConfig`

### 3. Circuit Breaker ✅
- **`base_client.py`** — в `__init__` создается экземпляр `CircuitBreaker` с параметрами из `PipelineConfig`:
  - `failure_threshold=CIRCUIT_FAILURE_THRESHOLD`
  - `recovery_timeout=CIRCUIT_RECOVERY_TIMEOUT`
- `call()` → `_call_with_circuit_breaker()` → через `cb.call_async()`
- При `CircuitBreakerError` — возвращается `mock_response` как fallback

## Тесты
- Все 349 тестов проходят (13.7s)
- `test_base_client.py` — 14 тестов (включая real-mode с circuit breaker)

## Файлы изменений

| Файл | Изменение |
|------|-----------|
| `app/core/trace.py` | **NEW** — Trace ID contextvar + фильтр |
| `app/core/logging_config.py` | TraceIdFilter в формат |
| `app/main.py` | Trace middleware |
| `app/models/pipeline.py` | trace_id поле в Task |
| `app/core/pipeline/orchestrator.py` | Проброс trace_id в Task и Celery |
| `app/services/base_client.py` | tenacity retry + circuit breaker |
| `app/tasks/pipeline_formation.py` | trace_id в аргументы задач |
| `specificity.md` | Обновлено |
