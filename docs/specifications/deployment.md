# Развёртывание (Deployment) — P8-6

> **Версия**: 0.1 (17.06.2026)
> **Источник**: план 5.06 P8-6, P11-5.
> **Статус**: 📝 документация-черновик. Финальная версия — после Sprint 3.

## 1. Архитектура Docker-сетей

```
┌─────────────────────────────────────────────────────────────┐
│  Docker-сеть `public` (мост в Nginx / внешний LB)         │
│  ┌──────────────────┐                                       │
│  │  Nginx :443      │  (reverse proxy, TLS termination)     │
│  └────────┬─────────┘                                       │
│           │                                                  │
│  ┌────────▼─────────┐                                       │
│  │  Web UI (SSR)    │  :3000 (внутри `public`)              │
│  └────────┬─────────┘                                       │
│           │ HTTP                                             │
└───────────┼──────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│  Docker-сеть `internal` (--internal, НЕ маршрутизируется)  │
│                                                              │
│  ┌────────────┐    ┌─────────────┐    ┌────────────┐       │
│  │  Gateway   │───▶│ Orchestrator│───▶│ Auth       │       │
│  │  :8080     │    │ :8081       │    │ :8082      │       │
│  └─────┬──────┘    └──────┬──────┘    └────────────┘       │
│        │                  │                                  │
│        │  ┌───────────────┼──────────────┐                  │
│        │  │               │              │                  │
│        ▼  ▼               ▼              ▼                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Query    │  │ Registry │  │ RAG-Srch │  │ RAG-Bld  │    │
│  │ :8083    │  │ :8084    │  │ :8091    │  │ :8090    │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Parser   │  │ OCR      │  │ Converter│  │ Integ.   │    │
│  │ :8087    │  │ :8088    │  │ :8086    │  │ :8085    │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                                                              │
│  ┌──────────┐                                               │
│  │ Analyse  │  (заморожен)                                  │
│  │ :8089    │                                               │
│  └──────────┘                                               │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│  Docker-сеть `data` (БД + storage)                          │
│  ┌──────────────┐  ┌─────────┐  ┌──────────┐  ┌────────┐  │
│  │ PostgreSQL   │  │ MinIO   │  │ Redis    │  │ TEI    │  │
│  │ :5432        │  │ :9000   │  │ :6379    │  │ :8080  │  │
│  └──────────────┘  └─────────┘  └──────────┘  └────────┘  │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│  Docker-сеть `signoz-network` (observability, --internal)  │
│  ┌──────────────┐  ┌─────────┐  ┌──────────┐              │
│  │ SigNoz UI    │  │ OTel    │  │ ClickHse │              │
│  │ :3301        │  │ :4317   │  │ :8123    │              │
│  └──────────────┘  └─────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## 2. docker-compose.yml (упрощённый шаблон)

```yaml
version: "3.9"

networks:
  public:
    driver: bridge
  internal:
    internal: true   # НЕ маршрутизируется во внешний мир
  data:
    internal: true
  signoz-network:
    internal: true

services:
  nginx:
    image: nginx:alpine
    networks: [public]
    ports: ["443:443"]
    volumes: ["./nginx.conf:/etc/nginx/nginx.conf:ro"]

  web-ui:
    image: pkb/web-ui:latest
    networks: [public]
    expose: ["3000"]
    depends_on: [gateway]

  gateway:
    image: pkb/gateway:latest
    networks: [public, internal]
    expose: ["8080"]   # НЕ публикуется в host
    environment:
      - AUTH_SERVICE_URL=http://auth:8082
      - ORCHESTRATOR_URL=http://orchestrator:8081
      - REGISTRY_URL=http://registry:8084
      - QUERY_URL=http://query:8083
      - INTEGRATION_URL=http://integration:8085
      - ANALYSE_URL=http://analyse:8089
    depends_on: [orchestrator, auth, registry, query]

  orchestrator:
    image: pkb/orchestrator:latest
    networks: [internal, data]
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/pkb
      - MINIO_URL=http://minio:9000
      - REDIS_URL=redis://redis:6379
    depends_on: [postgres, minio, redis]

  auth:
    image: pkb/auth:latest
    networks: [internal, data]
    depends_on: [postgres, redis]

  # ... остальные сервисы по аналогии

  postgres:
    image: postgres:15
    networks: [data]
    environment:
      - POSTGRES_DB=pkb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes: ["pgdata:/var/lib/postgresql/data"]

  minio:
    image: minio/minio
    networks: [data]
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=minio
      - MINIO_ROOT_PASSWORD=minio123

  redis:
    image: redis:7
    networks: [data]

  tei:
    image: ghcr.io/huggingface/text-embeddings-inference:latest
    networks: [data, internal]
    command: --model-id BAAI/bge-reranker-v2-m3-int8 --port 8080

  signoz-otel-collector:
    image: signoz/signoz-otel-collector:latest
    networks: [signoz-network, internal]
    expose: ["4317"]
    environment:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://signoz-otel-collector:4317

volumes:
  pgdata:
```

## 3. Health-checks

| Endpoint | Назначение | Кто проверяет |
|----------|-----------|---------------|
| `GET /health/live` | Процесс жив (livenessProbe) | k8s / Docker HEALTHCHECK |
| `GET /health/ready` | Готовность принимать трафик (readinessProbe) | k8s / Docker |
| `GET /health` | Полный статус (для debugging) | on-call инженер |

См. `docs/architecture/monitoring.md` §3 для подробностей.

## 4. Backup и restore

| Компонент | Что бэкапить | Как часто | Retention |
|-----------|--------------|-----------|-----------|
| PostgreSQL | Полный дамп + WAL | Ежедневно + инкрементальный WAL | 30 дней |
| MinIO | `files` бакет (исходные документы) | Еженедельно | 1 год |
| MinIO | `images` бакет | Ежемесячно | 90 дней |
| Redis | AOF + RDB | При каждом flush | 7 дней |
| SigNoz/ClickHouse | Метрики и логи | Не критично (можно пересоздать) | 30 дней |

## 5. Связанные документы

- `docs/architecture/monitoring.md` — SigNoz, OTel, SLO, алерты.
- `docs/specifications/registry_resolver_spec.md` — cron-задачи.
- `docs/api/common_api.md` §«Аутентификация service-to-service» — детали сетевой изоляции.
- Обсуждения 16.06 (микросервисы) — Docker-сети.
- План 5.06 P0-6, P8-6, P11-5.
