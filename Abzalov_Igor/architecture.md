# ARCHITECTURE.md

# System Architecture — RAG Builder Service

---

# SYSTEM PURPOSE

RAG Builder Service отвечает за построение векторного индекса документов для семантического поиска.

Сервис:

* получает нормализованный JSON
* выполняет chunking
* генерирует embeddings
* сохраняет данные в PostgreSQL + pgvector
* предоставляет статус индексирования
* удаляет индекс документа

---

# SOURCE OF TRUTH (IMMUTABLE)

Agents MUST read BEFORE implementation.

## API

`C:\Users\Игорь\projects\PKB\PKB_neuroassistant\docs\api\rag_builder_service_api.md`

## Pipeline

`C:\Users\Игорь\projects\PKB\PKB_neuroassistant\docs\pipelines\pipeline2-indexation.md`

## Input Schema

`C:\Users\Игорь\projects\PKB\PKB_neuroassistant\docs\schema\document3_for_rag.json`

## Database Models

`C:\Users\Игорь\projects\PKB\PKB_neuroassistant\docs\database\db_diagrams.md`

Agents are FORBIDDEN to modify these files.

---

# HIGH LEVEL ARCHITECTURE

```text id="7k2d91"
                    +-------------------+
                    | FastAPI API       |
                    | Port 8090         |
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    | Service Layer     |
                    +---------+---------+
                              |
               +--------------+--------------+
               |                             |
               v                             v
    +-------------------+         +-------------------+
    | Chunking Engine   |         | Embedding Engine  |
    +-------------------+         +-------------------+
               |                             |
               +--------------+--------------+
                              |
                              v
                    +-------------------+
                    | Repository Layer  |
                    +---------+---------+
                              |
                              v
               +-------------------------------+
               | PostgreSQL 16 + pgvector      |
               +-------------------------------+
```

---

# ARCHITECTURAL PRINCIPLES

## Mandatory Principles

* async-first architecture
* deterministic processing
* strict layering
* isolated business logic
* repository abstraction
* immutable contracts

---

# LAYER DEFINITIONS

## 1. API Layer

Responsibilities:

* request validation
* JWT authentication
* OpenAPI generation
* response serialization
* longpoll endpoints

Forbidden:

* business logic
* SQL
* chunking
* embedding generation

---

## 2. Service Layer

Responsibilities:

* orchestration
* transaction coordination
* indexing pipeline execution

Rules:

* pure business logic
* repository access only via interfaces
* no HTTP dependencies

---

## 3. Chunking Layer

Responsibilities:

* semantic chunking
* protected spans handling
* token counting
* table chunking

Rules:

* max 512 tokens
* deterministic output
* stable chunk IDs

---

## 4. Embedding Layer

Responsibilities:

* OpenAI-compatible embedding API integration
* batching
* retries
* vector validation

Rules:

* vector dimensions immutable
* timeout-safe
* retry-safe
* async execution only

---

## 5. Repository Layer

Responsibilities:

* database access
* vector persistence
* transactional operations

Rules:

* SQLAlchemy 2.x only
* async sessions only
* no business logic

---

# DATABASE ARCHITECTURE

## PostgreSQL

Version:

* PostgreSQL 16.14

## pgvector

Version:

* pgvector 0.8.2

## Connection

```text id="31fjq8"
postgresql://pkb_user:pkb_pass@localhost:5433/pkb_db
```

---

# VECTOR STORAGE

Stored entities:

* chunks
* embeddings
* metadata
* indexing status

Vector index requirements:

* cosine similarity
* ANN index support
* batch insert optimization

---

# INDEXATION FLOW

1. document accepted
2. schema validation
3. chunk generation
4. embedding generation
5. vector persistence
6. status update

---

# LONGPOLL ARCHITECTURE

Flow:

1. client requests status
2. API checks current state
3. waits asynchronously
4. returns final status

---

# OBSERVABILITY

Mandatory:

* structured logs
* correlation IDs
* request tracing
* DB timing metrics

---

# SECURITY

Required:

* JWT access token validation
* refresh token flow
* env-based secrets
* no secrets in repository
* input validation everywhere

---

# DOCKER ARCHITECTURE

Containers:

* FastAPI
* PostgreSQL
* Docker network

Rules:

* non-root containers
* healthchecks mandatory
* deterministic builds

---

# FORBIDDEN ARCHITECTURE VIOLATIONS

NEVER:

* bypass service layer
* embed SQL in routes
* mutate Source of Truth
* duplicate schema definitions
* access DB directly from API layer
* use sync DB sessions

---

# PERFORMANCE TARGETS

API:

* p95 < 300ms for status endpoints

Chunking:

* deterministic runtime

Embedding:

* batch optimized

DB:

* indexed vector search only

---

# DEPLOYMENT TARGET

Primary runtime:

* Docker Compose

Service Port:

* 8090
