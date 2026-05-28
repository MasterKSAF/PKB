# Docker Deployment Guide

## Цель
Пошаговый деплой RAG Builder Service в Docker с PostgreSQL 16 + pgvector 0.8.2.

## Предусловия
- Docker Desktop установлен.
- Свободны порты:
  - `8090` для API
  - `5433` для PostgreSQL на хосте

## 1. Поднять PostgreSQL + pgvector

```powershell
docker pull pgvector/pgvector:pg16

docker run -d --name pkb-pg16 `
  -e POSTGRES_USER=pkb_user `
  -e POSTGRES_PASSWORD=pkb_pass `
  -e POSTGRES_DB=pkb_db `
  -p 5433:5432 `
  -v pkb_pgdata:/var/lib/postgresql/data `
  pgvector/pgvector:pg16
```

Проверка:
```powershell
docker exec pkb-pg16 psql -U pkb_user -d pkb_db -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT extversion FROM pg_extension WHERE extname='vector';"
```
Ожидается `0.8.2` (или выше 0.7).

## 2. Подготовить .env
Создайте `.env` рядом с `.env.example`:
```env
APP_PORT=8090
DB_HOST=host.docker.internal
DB_PORT=5433
DB_NAME=pkb_db
DB_USER=pkb_user
DB_PASSWORD=pkb_pass
DATABASE_URL=
LOG_LEVEL=DEBUG
LOG_DIR=logs
LOG_FILE=rag_builder.log
JWT_SECRET=change-me
EMBEDDING_API_URL=http://host.docker.internal:8000/v1/embeddings
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_TIMEOUT=30
EMBEDDING_DIM=1536
VECTOR_DIMENSION=1536
CHUNK_SIZE=512
CHUNK_MAX_TOKENS=512
MAX_TOKENS=512
CHUNK_DEFAULT_STRATEGY=semantic_512
API_PREFIX=/api/v1
DEFAULT_LONGPOLL_SECONDS=15
```

## 3. Собрать образ приложения
Из папки `Abzalov_Igor`:

```powershell
docker build -t rag-builder-service:local -f Dockerfile .
```

Если видите ошибку `docker buildx build requires 1 argument`, значит команда запущена без последнего аргумента `.`

## 4. Запустить контейнер приложения

```powershell
docker run -d --name rag-builder-service `
  --env-file .env `
  -p 8090:8090 `
  -v ${PWD}\logs:/app/logs `
  rag-builder-service:local
```

## 5. Проверить работоспособность

```powershell
curl http://127.0.0.1:8090/openapi.json
```
или открываем в браузере:  http://127.0.0.1:8090/docs


Проверить логи:
```powershell
docker logs rag-builder-service --tail 200
Get-ChildItem .\logs
```

## 6. Остановить и удалить

```powershell
docker stop rag-builder-service pkb-pg16
docker rm rag-builder-service pkb-pg16
```

