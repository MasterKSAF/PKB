# Runbook После Git Pull

## Для кого
Инструкция для разработчика, который:
- сделал `git pull`
- хочет поднять проект локально
- хочет получить сразу PostgreSQL + `rag-builder-service`

## Предусловия
- установлен Docker Desktop
- свободны порты:
  - `8090` для API
  - `5433` для PostgreSQL

## 1. Перейти в папку проекта

```powershell
cd C:\Users\Игорь\projects\PKB\PKB_neuroassistant\Abzalov_Igor
```

## 2. Создать `.env`

Если файла нет, создать его из примера:

```powershell
Copy-Item .env.example .env
```

## 3. Заполнить обязательные переменные

Минимально проверить:

```env
APP_PORT=8090
DB_HOST=host.docker.internal
DB_PORT=5433
DB_NAME=pkb_db
DB_USER=pkb_user
DB_PASSWORD=pkb_pass
DATABASE_URL=

EMBEDDING_API_URL=https://api.openai.com/v1/embeddings
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_API_KEY=your_openai_api_key

VECTOR_DIMENSION=1536
EMBEDDING_DIM=1536
```

Важно:
- `EMBEDDING_PROVIDER` должен быть именно `openai_compatible`
- токен OpenAI должен лежать в `EMBEDDING_API_KEY`
- в `EMBEDDING_PROVIDER` нельзя вставлять токен
- `DATABASE_URL` лучше оставить пустым: `DATABASE_URL=`

## 4. Поднять весь стек одной командой

```powershell
docker compose up -d --build
```

Что произойдет:
- поднимется контейнер `pkb-pg16`
- поднимется контейнер `rag-builder-service`
- сервис дождется готовности PostgreSQL
- Alembic-миграции выполнятся автоматически
- таблицы `rag.*` создадутся автоматически

## 5. Проверить, что все запустилось

```powershell
docker compose ps
docker logs rag-builder-service --tail 200
curl.exe http://127.0.0.1:8090/api/v1/health
```

Ожидаемо:
- в логах есть `migrations applied successfully`
- health отвечает `200`

## 6. Проверить OpenAPI

Открыть в браузере:

```text
http://127.0.0.1:8090/docs
```

## 7. Остановить проект

```powershell
docker compose down
```

Если нужно удалить и volume PostgreSQL:

```powershell
docker compose down -v
```

## 8. Частые проблемы

### Контейнер приложения не видит БД

Проверить:

```powershell
docker compose ps
docker logs rag-builder-service --tail 200
docker logs pkb-pg16 --tail 200
```

### Ошибка с OpenAI embeddings

Проверить в `.env`:

```env
EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_API_KEY=...
```

Неправильно:

```env
EMBEDDING_PROVIDER=sk-...
```

### После изменения `.env` ничего не поменялось

`docker restart` не перечитывает `.env`.

Нужно:

```powershell
docker compose down
docker compose up -d --build
```
