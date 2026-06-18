# Мониторинг и наблюдаемость (Observability)

> **Версия**: 1.0 (17.06.2026)
> **Источник**: план `5.docs_action_plan_17_06.md` P8-8, P11-5, P11-6, P11-7, P11-8, P11-9.
> **Источник обсуждений**: 16.06 (микросервисы — SigNoz + OpenTelemetry + ClickHouse), 08.06 (Infinity, метрики), 17.06 (5 шагов внедрения, service_checker).

## 1. Архитектура наблюдаемости

```
┌────────────────────────────────────────────────────────────────┐
│                    Docker-сеть `internal`                       │
│                                                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │  Auth   │  │  Orch.  │  │  Query  │  │  ...    │  OTEL SDK│
│  │  :8082  │  │  :8081  │  │  :8083  │  │         │ ──────┐ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └─────────┘       │ │
│       │             │             │                          │ │
│       └─────────────┼─────────────┴──────────────────────────┘ │
│                     │                                          │
│              OTLP Export (gRPC :4317)                          │
│                     │                                          │
└─────────────────────┼──────────────────────────────────────────┘
                      ▼
              ┌───────────────────┐
              │  SigNoz           │
              │  (Docker-сеть     │
              │   signoz-network) │
              │  ┌─────────────┐  │
              │  │ OTel-       │  │
              │  │ Collector   │  │
              │  │ :4317       │  │
              │  └──────┬──────┘  │
              │         │         │
              │  ┌──────▼──────┐  │
              │  │ ClickHouse  │  │
              │  │ (storage)   │  │
              │  └──────┬──────┘  │
              │         │         │
              │  ┌──────▼──────┐  │
              │  │ Query       │  │
              │  │ Service     │  │
              │  │ + Frontend  │  │
              │  └─────────────┘  │
              └───────────────────┘
```

**Стек:**
- **OpenTelemetry SDK** в каждом сервисе (Python: `opentelemetry-python` + `opentelemetry-instrumentation-fastapi`, `opentelemetry-instrumentation-sqlalchemy`, `opentelemetry-instrumentation-asyncpg`).
- **OTLP-экспорт** через `OTLPSpanExporter` → `signoz-otel-collector:4317` (gRPC).
- **SigNoz** (UI + Query Service) + **ClickHouse** (storage) внутри Docker-сети `signoz-network`.
- **Алерты** — Prometheus-формат через SigNoz Alerts → Slack / PagerDuty.

---

## 2. 5 шагов внедрения (P11-5, уточнение 17.06)

> **OpenTelemetry обязателен во всех сервисах без исключения.** Проверка наличия OTEL-инструментации — через `service_checker` (см. §7).

### Шаг 1: Развёртывание SigNoz

```bash
# Создать сеть (изолирована от internal)
docker network create signoz-network

# Запустить SigNoz + ClickHouse + OTel-Collector
git clone -b main https://github.com/SigNoz/signoz.git
cd signoz/deploy/docker
# Отредактировать .env: SIGNOZ_OTEL_COLLECTOR_ADDR=signoz-otel-collector:4317
docker compose -f docker-compose.yaml up -d
```

### Шаг 2: Добавление OTEL SDK в каждый сервис

В `pyproject.toml` (или `requirements.txt`) каждого сервиса:

```toml
opentelemetry-api = "^1.27.0"
opentelemetry-sdk = "^1.27.0"
opentelemetry-exporter-otlp-proto-grpc = "^1.27.0"
opentelemetry-instrumentation-fastapi = "^0.48b0"
opentelemetry-instrumentation-sqlalchemy = "^0.48b0"
opentelemetry-instrumentation-asyncpg = "^0.48b0"
opentelemetry-instrumentation-redis = "^0.48b0"
opentelemetry-instrumentation-celery = "^0.48b0"
opentelemetry-instrumentation-httpx = "^0.48b0"
opentelemetry-instrumentation-requests = "^0.48b0"
```

В `main.py` каждого сервиса (вызывается **до** создания FastAPI app):

```python
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

resource = Resource.create({
    "service.name": "rag-search",  # имя сервиса
    "service.version": "1.0.0",
    "deployment.environment": "production",
})

provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint="http://signoz-otel-collector:4317", insecure=True)
)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Затем инструментация FastAPI/SQLAlchemy/etc.
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)
```

### Шаг 3: Стандартизация span-имён

| Префикс | Пример | Описание |
|---------|--------|----------|
| `http.{method}.{route}` | `http.POST./api/v1/drafts` | HTTP-эндпоинт (FastAPI auto-instrumentation) |
| `db.{op}.{table}` | `db.INSERT.registry.documents` | SQL-операция (SQLAlchemy auto) |
| `parser.process` | — | Полный цикл парсинга |
| `parser.preview` | — | Preview-фаза парсинга |
| `ocr.process` | — | Полный цикл OCR |
| `ocr.preview` | — | Preview-фаза OCR |
| `converter.convert` | — | Полная конвертация |
| `rag.search` | — | Поиск чанков |
| `rag.build` | — | Индексация |
| `llm.generate` | — | Генерация ответа LLM |
| `cache.get` / `cache.set` | — | Операции с кешем |

**Обязательные span-атрибуты:**
- `service.name` (устанавливается через Resource)
- `service.version` (устанавливается через Resource)
- `deployment.environment` (`production` / `staging` / `development`)
- `user_id` (если применимо)
- `document_id`, `version_id`, `draft_id` (если применимо)
- `request_id` (из `X-Request-ID`)
- `error_code` (при ошибке)

### Шаг 4: Экспорт OTLP в `signoz-otel-collector:4317`

Конфигурация в `app_settings.yaml` каждого сервиса:

```yaml
observability:
  otel:
    enabled: true
    endpoint: "signoz-otel-collector:4317"
    insecure: true
    service_name: "rag-search"
    service_version: "1.0.0"
    deployment_environment: "production"
```

### Шаг 5: Дашборды и алерты в SigNoz

**Дашборды (см. §4 SLO/SLI):**
1. **Latency overview** — p50/p95/p99 по сервисам.
2. **Error rate** — 5xx / 4xx по сервисам.
3. **RPS** — запросы/сек по сервисам и эндпоинтам.
4. **Pipeline 2 Indexing duration** — p95 времени индексации.
5. **RAG Search latency** — p95 поиска.
6. **LLM usage** — calls, tokens, errors.

**Алерты** — см. §6.

---

## 3. Health-checks уровня зависимостей (P11-6)

> **Расширение**: `/health/ready` vs `/health/live` для всех микросервисов.

| Endpoint | Назначение | Проверки |
|----------|-----------|----------|
| `GET /health/live` | Процесс жив (k8s livenessProbe) | Минимальная — процесс отвечает, не завис |
| `GET /health/ready` | Готовность принимать трафик (k8s readinessProbe) | Проверка зависимостей: БД, Redis, MinIO, SigNoz (OTEL), другие сервисы |
| `GET /health` (legacy) | Полный статус (для debugging) | Все проверки + uptime + version |

**Проверки по сервисам:**

| Сервис | БД | MinIO | Redis | SigNoz OTEL | Другие |
|--------|----|----|-------|-------------|--------|
| Gateway | — | — | ✅ rate limit | ✅ exporter | ✅ upstream (auth) |
| Orchestrator | ✅ | ✅ | ✅ celery | ✅ | ✅ registry, parser/ocr |
| Auth | ✅ | — | ✅ | ✅ | — |
| Query | ✅ | — | ✅ | ✅ | ✅ rag-search |
| Registry | ✅ | — | — | ✅ | — |
| Integration | ✅ | ✅ | — | ✅ | ✅ meridian API |
| Converter-validator | — | — | — | ✅ | ✅ registry (read), LLM |
| Parser | — | ✅ | — | ✅ | — |
| OCR | — | ✅ | — | ✅ | — |
| RAG Builder | ✅ | — | — | ✅ | — |
| RAG Search | ✅ | — | — | ✅ | — |
| Analyse | ✅ | — | — | ✅ | — |

**Формат ответа `/health/ready`:**

```json
{
  "status": "ok",
  "service": "rag-search",
  "version": "1.0.0",
  "uptime_seconds": 123456,
  "checks": {
    "database": {"status": "ok", "latency_ms": 5},
    "redis": {"status": "ok", "latency_ms": 2},
    "otel_exporter": {"status": "ok", "latency_ms": 10},
    "upstream_registry": {"status": "ok", "latency_ms": 15}
  }
}
```

**При недоступности зависимости** — `status: degraded` (не `error`), но `ready=false`. k8s уберёт под из балансировки, но **не** будет перезапускать.

---

## 4. SLO/SLI (P11-7, 17.06.2026)

| SLI | SLO | Окно измерения | Источник |
|-----|-----|----------------|----------|
| RAG Search latency p95 | ≤ 500 мс | 28 дней | OTel `rag.search` span |
| RAG Search recall@10 | ≥ 0.85 | 7 дней | `rag_evaluation_methodology.md` |
| Indexing p95 | ≤ 60 с CPU / ≤ 15 с GPU | 28 дней | OTel `rag.build` span |
| Parser/OCR success rate | ≥ 99% | 28 дней | `pipeline.tasks` status |
| Gateway 5xx rate | ≤ 0.1% | 28 дней | OTel HTTP server metrics |
| Health-check `/ready` success | ≥ 99.5% | 28 дней | k8s probe |
| OpenTelemetry exporter success | ≥ 99.9% | 28 дней | OTel self-telemetry |

**Алерты при нарушении SLO** — см. §6.

---

## 5. Метрики (P11-5)

| Метрика | Тип | Описание |
|---------|-----|----------|
| `http_server_requests_total{method,path,status}` | counter | Количество HTTP-запросов |
| `http_server_request_duration_seconds{method,path,status}` | histogram | Длительность HTTP-запросов |
| `db_pool_connections{state}` | gauge | Соединения в пуле БД (active, idle) |
| `rag_search_duration_seconds` | histogram | Длительность поиска |
| `rag_search_results_count` | histogram | Количество результатов |
| `rag_build_duration_seconds` | histogram | Длительность индексации |
| `rag_build_chunks_count` | histogram | Количество чанков в документе |
| `llm_request_duration_seconds{model}` | histogram | Длительность LLM-запроса |
| `llm_tokens_total{model,type}` | counter | prompt/completion tokens |
| `llm_errors_total{model,code}` | counter | Ошибки LLM |
| `pipeline_tasks_in_progress{stage}` | gauge | Задачи в обработке по стадиям |
| `pipeline_tasks_failed_total{stage,error_code}` | counter | Упавшие задачи |
| `audit_events_total{action,entity_type}` | counter | События аудита (P11-4) |

---

## 6. Алерты (P11-8, 17.06.2026)

> **Формат**: Prometheus-правила → SigNoz Alerts → Slack/PagerDuty.

| ID | Алерт | Условие | Длительность | Severity | Действие |
|----|-------|---------|--------------|----------|----------|
| A-01 | Gateway 5xx > 1% | `rate(http_server_requests_total{status=~"5.."}[5m]) / rate(http_server_requests_total[5m]) > 0.01` | 5 мин | warning | Slack #alerts |
| A-02 | RAG Search p95 > 1 с | `histogram_quantile(0.95, rag_search_duration_seconds[5m]) > 1.0` | 5 мин | warning | Slack #alerts |
| A-03 | RAG Search p95 > SLO 500 мс (1 час) | `histogram_quantile(0.95, rag_search_duration_seconds[1h]) > 0.5` | 1 час | critical | PagerDuty |
| A-04 | Indexing p95 > SLO (1 час) | `histogram_quantile(0.95, rag_build_duration_seconds[1h]) > 60` (или `> 15` для GPU) | 1 час | critical | PagerDuty |
| A-05 | Failed task > 30 мин | `time() - max(pipeline_tasks_failed_total{stage="..."}) > 1800` | 30 мин | error | Slack #alerts |
| A-06 | `indexed → failed` rate > 0 | `rate(pipeline_tasks_failed_total{stage="integrity_check"}[5m]) > 0` | 5 мин | error | Slack #alerts |
| A-07 | `pending_index` > 1 час | `max(pipeline_tasks_in_progress{stage="pending_index"}) > 0 AND time() - max(pipeline_tasks_started_at{stage="pending_index"}) > 3600` | 1 час | warning | Slack #alerts |
| A-08 | MinIO disk usage > 80% | `minio_disk_used_percent > 80` | 5 мин | warning | Slack #alerts |
| A-09 | OTEL exporter down | `up{job="otel-collector"} == 0` | 1 мин | critical | PagerDuty |
| A-10 | DB connection pool > 90% | `db_pool_connections{state="active"} / db_pool_connections{state="max"} > 0.9` | 5 мин | warning | Slack #alerts |
| A-11 | Redis недоступен | `redis_up == 0` | 1 мин | warning | Slack #alerts (rate limit отключён — см. common_api.md) |
| A-12 | Health `/ready` failing | `kube_pod_status_ready{condition="ready"} == 0` | 5 мин | critical | PagerDuty |
| A-13 | Audit log gap | `time() - max(audit_events_total.timestamp) > 600` | 10 мин | warning | Slack #alerts |

---

## 7. `service_checker` (P11-9, 17.06.2026)

> **Назначение**: автопроверка сервисов на соответствие стандарту observability. Запускается в CI (PR-чек) и post-deploy.

### 7.1. Что проверяет

1. **OTEL SDK инициализирован в `main.py`**: парсинг AST / grep наличия `TracerProvider`/`OTLPSpanExporter`.
2. **OTLP endpoint**: парсинг `app_settings.yaml` — наличие `observability.otel.endpoint` со значением `signoz-otel-collector:4317`.
3. **Обязательные span-атрибуты**: парсинг кода на наличие `Resource.create({...})` с `service.name`, `service.version`, `deployment.environment`.
4. **Структура логов**: парсинг `LOG_PII_FIELDS` в `app_settings.yaml` — должны быть указаны `password, access_token, refresh_token` (минимум).
5. **Correlation IDs**: парсинг middleware на наличие пробрасывания `X-Request-ID` / `X-Trace-ID`.
6. **Health-checks**: наличие `/health/ready` и `/health/live` endpoints с правильной логикой (есть тесты).

### 7.2. Запуск

```bash
# В CI (после успешных unit/integration тестов)
python -m service_checker \
  --service-path backend/services/rag_search/ \
  --config-path backend/services/rag_search/app_settings.yaml \
  --report-path /var/log/service_checker/rag_search.json

# Post-deploy (в k8s Job)
kubectl create job --from=cronjob/service-checker-postdeploy service-checker-$(date +%s)
```

### 7.3. Формат отчёта

```json
{
  "service": "rag-search",
  "version": "1.0.0",
  "checked_at": "2026-06-18T14:30:00Z",
  "checks": {
    "otel_sdk_initialized": {"status": "ok"},
    "otlp_endpoint_configured": {"status": "ok", "endpoint": "signoz-otel-collector:4317"},
    "required_span_attributes": {"status": "ok", "attributes": ["service.name", "service.version", "deployment.environment"]},
    "log_pii_filter": {"status": "ok", "fields": ["password", "access_token", "refresh_token"]},
    "correlation_ids": {"status": "ok", "headers": ["X-Request-ID", "X-Trace-ID"]},
    "health_endpoints": {"status": "ok", "endpoints": ["/health/live", "/health/ready"]}
  },
  "overall_status": "ok"
}
```

### 7.4. CI-интеграция

- **PR-чек**: `service_checker` запускается параллельно с unit-тестами. При `overall_status != ok` — блокируется merge.
- **Post-deploy**: Job в k8s, запускается через 5 мин после деплоя. Отчёт сохраняется в `/var/log/service_checker/<service>.json`, отправляется в SigNoz как лог-событие.

---

## 8. Связанные документы

- `docs/api/common_api.md` — общее описание логирования, PII, health-checks.
- `docs/api/gateway_service_api.md` — health-check агрегатор.
- `docs/audit/audit_06_06_2026.md` — D43 (неполные health-checks, до фикса).
- `docs/architecture/service_dependencies.md` (NEW) — TEI, Infinity, OTEL Collector.
- `docs/architecture/service_checker.md` (NEW) — детальное описание утилиты.
- Обсуждения 16.06 (микросервисы), 08.06 (Infinity).
- План 5.06.2026: P8-8, P11-5, P11-6, P11-7, P11-8, P11-9.
