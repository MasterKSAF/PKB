# Зависимости сервисов (Service Dependencies)

> **Версия**: 1.0 (17.06.2026)
> **Источник**: P9-1 (план 5.06), `docs_plans/errors/ошибки запуска сервисов.md`.

## 1. Python-пакеты по сервисам

### Gateway (gateway:8080)
```
fastapi==0.115.*
uvicorn[standard]==0.32.*
httpx==0.27.*
pyjwt==2.9.*
pydantic==2.*
python-multipart==0.0.*
redis==5.*
prometheus-client==0.21.*
structlog==24.*
opentelemetry-api==1.27.*
opentelemetry-sdk==1.27.*
opentelemetry-distro==0.48b0
opentelemetry-exporter-otlp==1.27.*
opentelemetry-instrumentation-fastapi==0.48b0
opentelemetry-instrumentation-httpx==0.48b0
opentelemetry-propagator-b3==1.27.*
python-json-logger==2.0.4
setuptools<70
```

### Orchestrator (orchestrator:8081)
```
fastapi, uvicorn, httpx
celery[redis]==5.4.*
redis==5.*
sqlalchemy[asyncio]==2.0.*
asyncpg==0.30.*
alembic==1.13.*
pydantic==2.*
python-multipart
boto3==1.35.*             # MinIO
prometheus-client
structlog
opentelemetry-*
```

### Auth (auth:8082)
```
fastapi, uvicorn, httpx
sqlalchemy[asyncio], asyncpg, alembic
passlib[bcrypt]==1.7.*
bcrypt==4.2.*
pyjwt
python-multipart
email-validator>=2.0  # P9-2: для валидации email
prometheus-client
structlog
opentelemetry-*
```

### Query Service (query:8083)
```
fastapi, uvicorn, httpx
sqlalchemy[asyncio], asyncpg
httpx
openai==1.50.*           # для deepseek-4-flash через OpenAI-совместимое API
tiktoken==0.7.*
prometheus-client
structlog
opentelemetry-*
```

### Registry (registry:8084)
```
fastapi, uvicorn
sqlalchemy[asyncio], asyncpg, alembic
pgvector==0.3.*
prometheus-client
structlog
opentelemetry-*
```

### Integration (integration:8085)
```
fastapi, uvicorn
sqlalchemy[asyncio], asyncpg
boto3                    # MinIO
httpx                    # Меридиан API
prometheus-client
structlog
opentelemetry-*
```

### Converter-validator (converter-validator:8086)
```
fastapi, uvicorn
openai==1.50.*           # LLM
httpx
pydantic
prometheus-client
structlog
opentelemetry-*
```

### Parser (parser:8087)
```
fastapi, uvicorn
pypdf==5.*
pdfplumber==0.11.*
python-docx==1.1.*
docling==2.1.*           # парсинг сложных PDF
boto3                    # MinIO
pydantic
prometheus-client
structlog
opentelemetry-*
```

### OCR (ocr:8088)
```
fastapi, uvicorn
paddleocr==2.7.*
pytesseract==0.3.*
easyocr==1.7.*
Pillow==10.*
boto3                    # MinIO
prometheus-client
structlog
opentelemetry-*
```

### RAG Builder (rag-builder:8090)
```
fastapi, uvicorn
sqlalchemy[asyncio], asyncpg
pgvector
httpx                    # Infinity / Qwen3 API
tiktoken                 # подсчёт токенов
prometheus-client
structlog
opentelemetry-*
```

### RAG Search (rag-search:8091)
```
fastapi, uvicorn
sqlalchemy[asyncio], asyncpg
pgvector
httpx                    # TEI rerank
prometheus-client
structlog
opentelemetry-*
```

### Analyse (analyse:8089)
```
fastapi, uvicorn
sqlalchemy[asyncio], asyncpg
pydantic
prometheus-client
structlog
opentelemetry-*
```

## 2. Внешние сервисы

| Сервис | URL/Endpoint | Где используется | Аутентификация |
|--------|--------------|-------------------|----------------|
| **MinIO** (CAS) | `http://minio:9000` | Все сервисы хранят/читают файлы | Access Key / Secret Key |
| **PostgreSQL 15+** | `postgresql://postgres:5432/pkb` | Все сервисы с доступом к БД | user / password |
| **pgvector** | (расширение PostgreSQL) | Registry, RAG Builder, RAG Search | — |
| **Redis 7** | `redis://redis:6379` | Gateway (idempotency), Orchestrator (Celery), Auth (sessions) | (без пароля в dev) |
| **Qwen3-Embedding-4B API** (внешний) | `app_settings.rag.embedding_api.endpoint` | RAG Builder, RAG Search | API key в `app_settings` |
| **deepseek 4 flash API** (внешний) | `app_settings.llm.api_url` | Query Service, Converter-validator | API key в `app_settings` |
| **TEI** (text-embeddings-inference, локальный) | `http://tei:8080` | RAG Builder (embeddings), RAG Search (rerank) | (без auth, в internal-сети) |
| **Infinity** (опционально, локальный) | `http://infinity:8080` | RAG Builder (вместо внешнего Qwen3) | (без auth, в internal-сети) |
| **SigNoz OTLP** | `http://signoz-otel-collector:4317` | Все сервисы (мониторинг, логи) | (без auth, в internal-сети) |
| **ClickHouse** | `http://clickhouse:8123` | SigNoz (storage) | (внутренний) |
| **Nginx** (reverse proxy) | `https://example.com:443` | Web UI | TLS termination |

## 3. Структура mock-роутера Gateway (P9-3)

> **Назначение**: для dev/test Gateway может объединять все сервисы в одно FastAPI-приложение. **Точный путь к mock-файлу**: `backend/dev/gateway_mock.py` (требует уточнения после ревизии `backend/`). Документация описывает контракт, а не привязана к пути файла.

```python
# Структура mock-роутера (концепт, не готовый код)
from fastapi import FastAPI

app = FastAPI(title="PKB Mock Gateway", version="0.1.0")

# Подключаемые модули (mock-роуты)
MOCK_ROUTES = {
    "/api/v1/auth": "mocks.auth",
    "/api/v1/drafts": "mocks.drafts",
    "/api/v1/documents": "mocks.documents",
    "/api/v1/chat": "mocks.chat",
    "/api/v1/text": "mocks.text",
    "/api/v1/registry": "mocks.registry",
    "/api/v1/meridian": "mocks.meridian",
    "/api/v1/analyse": "mocks.analyse",
    "/api/v1/system": "mocks.system",
}

# Auto-mount
for prefix, module_name in MOCK_ROUTES.items():
    module = __import__(module_name, fromlist=["router"])
    app.include_router(module.router, prefix=prefix)
```

В **production** Gateway — отдельный сервис (`:8080`), который проксирует запросы к реальным сервисам. Mock-роутер используется только в `ENV=development` или в интеграционных тестах.

## 4. Связанные документы

- `docs/specifications/deployment.md` — Docker-сети, развёртывание.
- `docs/architecture/monitoring.md` — SigNoz, OpenTelemetry, метрики.
- `docs/api/common_api.md` §«Межсервисное взаимодействие».
- `docs_plans/errors/ошибки запуска сервисов.md` — история проблем.
