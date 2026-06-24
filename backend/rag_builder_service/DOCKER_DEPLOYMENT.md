# Docker Deployment Guide

## Цель
Пошаговый деплой RAG Builder Service в Docker с PostgreSQL 16 + pgvector 0.8.2.

## Рекомендуемый вариант: Docker Compose

Из папки `Abzalov_Igor`:

```powershell
docker compose up -d --build
```

Compose сам:
- поднимет `pkb-pg16`
- дождется готовности PostgreSQL
- соберет `rag-builder-service`
- запустит Alembic-миграции при старте приложения
- создаст таблицы `rag.*`

Проверка:
```powershell
docker compose ps
docker logs rag-builder-service --tail 200
curl.exe http://127.0.0.1:8090/api/v1/health
```

Отдельная пошаговая инструкция для нового разработчика после `git pull`:
- [GITHUB_PULL_RUNBOOK.md](C:\Users\Игорь\projects\PKB\PKB_neuroassistant\Abzalov_Igor\GITHUB_PULL_RUNBOOK.md)

Остановка:
```powershell
docker compose down
```

Полное удаление вместе с volume PostgreSQL:
```powershell
docker compose down -v
```

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
Ожидается `0.8.2` (или выше `0.7`).

## 2. Подготовить `.env`
Создайте `.env` рядом с `.env.example`:
```env
APP_PORT=8090
DB_HOST=host.docker.internal
DB_PORT=5433
DB_NAME=pkb_db
DB_USER=pkb_user
DB_PASSWORD=pkb_pass
DATABASE_URL=
JWT_SECRET=change-me-at-least-32-characters
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRE_MINUTES=30
JWT_REFRESH_EXPIRE_MINUTES=10080
AUTH_USERNAME=admin
AUTH_PASSWORD=admin
LOG_LEVEL=DEBUG
LOG_DIR=logs
LOG_FILE=rag_builder.log
LOG_ROTATION=10 MB
LOG_RETENTION=14 days
LOG_COMPRESSION=zip
EMBEDDING_API_URL=https://api.openai.com/v1/embeddings
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_TIMEOUT=30
EMBEDDING_BATCH_SIZE=32
EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_API_KEY=
EMBEDDING_RETRIES=2
EMBEDDING_DIM=2048
VECTOR_DIMENSION=2048
CHUNK_SIZE=1024
CHUNK_MAX_TOKENS=1024
MAX_TOKENS=1024
CHUNK_DEFAULT_STRATEGY=semantic_1024
API_PREFIX=/api/v1
DEFAULT_LONGPOLL_SECONDS=15
MIGRATION_RETRIES=20
MIGRATION_RETRY_DELAY_SECONDS=3
```

Важно:
- `EMBEDDING_PROVIDER=openai_compatible`
- токен OpenAI хранить в `EMBEDDING_API_KEY`
- не подставлять токен в `EMBEDDING_PROVIDER`

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

Что теперь происходит при старте контейнера:
- контейнер сам выполняет `alembic upgrade head`
- если PostgreSQL еще не готов, контейнер делает ретраи
- после успешных миграций запускается `uvicorn`
- таблицы `rag` и `alembic_version` создаются автоматически

## 5. Проверить работоспособность

```powershell
curl http://127.0.0.1:8090/openapi.json
```

или откройте в браузере:
`http://127.0.0.1:8090/docs`

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

## 7. Когда что использовать
- `docker compose up -d --build` — лучший вариант для нового разработчика
- ручные `docker run ...` — если нужно отдельно управлять PostgreSQL и приложением
