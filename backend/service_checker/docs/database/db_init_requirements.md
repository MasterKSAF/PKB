# Требования к инициализации БД для сервисов

> **Для кого:** Разработчики всех backend-сервисов (Auth, Registry, Query, Orchestrator, RAG Builder, RAG Search, Integration и др.)
>
> **Суть:** Каждый сервис, работающий с PostgreSQL, обязан создавать свои таблицы при старте. Это гарантирует работоспособность сервиса как в Docker, так и при standalone-запуске.

---

## 1. Обязательный паттерн

Каждый сервис с таблицами в БД должен вызывать `Base.metadata.create_all(bind=engine)` **при старте**.

### Вариант A — lifespan (рекомендуется, FastAPI)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import create_engine
from .models import Base  # все модели импортированы в Base.metadata

# Синхронный engine
engine = create_engine(os.getenv("DATABASE_URL"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # create_all при старте (idempotent — безопасен при повторных запусках)
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)
```

### Вариант B — lifespan (async engine)

```python
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(os.getenv("DATABASE_URL"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
```

### Вариант C — init_db() для не-FastAPI сервисов

```python
def init_db():
    Base.metadata.create_all(bind=engine)
```

Вызвать при загрузке модуля или в startup-хуке фреймворка.

---

## 2. Что должно быть в сервисе

### 2.1 SQLAlchemy Base с моделями

```python
# models.py
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, ...

class Base(DeclarativeBase):
    pass

class Document(Base):
    __tablename__ = "documents"
    __table_args__ = {"schema": "registry"}
    
    id = Column(Integer, primary_key=True)
    ...
```

**Важно:** Все модели должны быть импортированы в момент вызова `create_all()`, иначе таблицы не создадутся.

### 2.2 Чтение конфигурации из окружения

```python
import os

DATABASE_URL = os.getenv("DATABASE_URL")  # приоритет
# или индивидуальные переменные:
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USERNAME", "postgres")
DB_PASS = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_DATABASE", "pkb_neuro")
```

**Не использовать** hardcoded `127.0.0.1`, `localhost` и т.п. — в Docker хост всегда `postgres`.

---

## 3. Примеры из существующих сервисов

| Сервис | Файл | Механизм | Статус |
|--------|------|----------|:------:|
| Auth | `auth_service/app/db/init_db.py` | `async def init_db` → `Base.metadata.create_all` | ✅ |
| Auth | `auth_service/app/main.py` | `lifespan` → `await init_db(db)` | ✅ |
| Query | `query_service/app/db.py` | `async def init_db` → `Base.metadata.create_all` | ✅ |
| Query | `query_service/app/main.py` | `lifespan` → `await init_db()` | ✅ |
| Orchestrator | `orchestrator_service/app/main.py` | `lifespan` → `conn.run_sync(Base.metadata.create_all)` | ✅ |
| Integration | `integration_service/api/v1/models.py` | `Base.metadata.create_all(bind=engine)` при импорте | ✅ |
| **Registry** | `registry_service/main.py` | ❌ **отсутствует** | 🔴 |
| **RAG Builder** | `rag_builder_service/rag_builder/main.py` | ❌ **отсутствует** | 🔴 |
| **RAG Search** | `rag_search_service/app/core/database.py` | `init_db_pool()` — только пул, без `create_all` | 🔴 |

---

## 4. Что НЕ нужно делать

### ❌ Не полагаться только на внешний SQL-скрипт

```python
# registry_service/main.py — ПЛОХО
# Таблицы создаются только через внешний дамп (setup_db.py®)
# При запуске сервиса вне Docker таблиц нет → 500 ошибки
```

### ❌ Не использовать hardcoded credentials

```python
DB_HOST = "127.0.0.1"  # ПЛОХО — не работает в Docker
```

### ❌ Не копировать setup_db.py в каждый сервис

`setup_db.py` — это утилита **service_checker** для Docker-окружения. Каждый сервис должен сам создавать свои таблицы при старте.

---

## 5. Проверка выполнения требований

Критерии приёма для каждого сервиса:

- [ ] Сервис запускается без предварительного выполнения `setup_db.py`
- [ ] SQLAlchemy модели определены и импортированы
- [ ] `Base.metadata.create_all()` вызывается при старте
- [ ] Таблицы создаются в правильной схеме (`registry`, `rag`, `public`)
- [ ] `DATABASE_URL` читается из переменных окружения
- [ ] Работает в Docker (хост `postgres`, порт `5432`)

---

## 6. Результаты проверки: кто и какие таблицы создаёт

Проверка всех сервисов, работающих с PostgreSQL — кто создаёт таблицы при старте, а кто нет.

| Сервис | Схема | Таблицы | Стартовый `create_all()` | Файл |
|--------|-------|---------|:------------------------:|:----:|
| Auth Service | `public` | `users`, `roles`, `audit`, `roles_history` и др. | ✅ `on_event startup` → `init_db()` | `auth_service/app/main.py` |
| Query Service | `public` | `sessions`, `messages`, `dialog_sessions` и др. | ✅ `lifespan` → `init_db()` | `query_service/app/main.py` |
| Orchestrator | `public` | `pipeline`, `pipeline_steps` и др. | ✅ `lifespan` → `Base.metadata.create_all()` | `orchestrator_service/app/main.py` |
| Integration | `public` | `documents`, `tasks` и др. | ✅ `Base.metadata.create_all()` при импорте модуля | `integration_service/api/v1/models.py` |
| **Registry** | **`registry`** | **~18 таблиц: `documents`, `document_sections`, `classifiers`, `terminology`, `enums` и др.** | **❌ НЕТ** | **`registry_service/main.py`** |
| **RAG Builder** | **`rag`** | **`document_chunks`** (с HNSW, GIN индексами, триггером tsv) | **❌ НЕТ** | **`rag_builder_service/src/rag_builder/api/app.py`** |
| RAG Search | `rag` | читает `document_chunks` | — (consumer, не создаёт) ✅ | — |

### Детально

#### Схема `registry` — должен создавать Registry Service

```sql
CREATE SCHEMA IF NOT EXISTS registry;

CREATE TABLE registry.documents (...);
CREATE TABLE registry.document_sections (...);
CREATE TABLE registry.classifiers (...);
CREATE TABLE registry.terminology (...);
CREATE TABLE registry.document_links (...);
CREATE TABLE registry.processing_history (...);
-- ~18 таблиц всего, полный дамп: backend/registry_service/install/1. db_dump.sql
```

Registry Service — единственный сервис, который знает полный набор своих таблиц.
Дамп в `install/` — это архивная копия, не механизм инициализации.

**Проблема:** `registry_service/main.py` не имеет lifespan, не вызывает `create_all()`.
Т.е. при запуске Registry вне Docker таблицы не создадутся → 500 ошибки.

#### Схема `rag` — должен создавать RAG Builder

```sql
CREATE SCHEMA IF NOT EXISTS rag;

CREATE TABLE IF NOT EXISTS rag.document_chunks (
    id          SERIAL PRIMARY KEY,
    section_id  INTEGER NOT NULL,
    document_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(1536),
    strategy    VARCHAR(32) NOT NULL,
    page        INTEGER,
    bbox        JSONB,
    confidence  FLOAT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON rag.document_chunks
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS idx_chunks_tsv ON rag.document_chunks USING gin (tsv);

CREATE TRIGGER trg_chunks_tsv BEFORE INSERT OR UPDATE OF content ON rag.document_chunks ...
```

RAG Builder имеет модели (`rag_builder_service/src/rag_builder/models/db.py`),
`engine` в `db/session.py`, но `create_app()` **не вызывает** `Base.metadata.create_all()`.

В тестах (`conftest.py`) create_all есть — значит для тестов создают, а для production — нет.

RAG Search — consumer, только читает `document_chunks`, создавать не должен. Это норма.

#### Схема `public` — создаётся каждым из сервисов

Auth, Query, Orchestrator, Integration — у всех есть `create_all()` при старте. Всё корректно.

### Что делать нерадивым

| Сервис | Нужно добавить | Пример из |
|--------|----------------|-----------|
| Registry | `lifespan` с `Base.metadata.create_all(bind=engine)` | Orchestrator `app/main.py` |
| RAG Builder | `Base.metadata.create_all(bind=engine)` в `create_app()` | Integration `models.py` |

**Задача service_checker** — проверять и сообщать, а не исправлять за сервисы.
`setup_db.py` инициализирует БД в Docker только для работы checker'а, но каждый сервис
должен уметь запускаться самостоятельно.
