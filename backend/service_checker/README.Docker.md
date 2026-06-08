# Docker-сборка PKB Neuroassistant

## Двухуровневая архитектура

### 1. Базовый образ (`Dockerfile.base`) — публикуется в registry

Содержит только среду выполнения:
- Python 3.13 + все pip-пакеты
- supervisor, libmagic1, libpq5
- ENV-переменные по умолчанию

**Не содержит** код сервисов, entrypoint, supervisord.conf.

```bash
# Сборка и публикация базового образа (делается один раз)
docker build -f backend/service_checker/docker/Dockerfile.base -t ghcr.io/pkb/neuro-base:latest .
docker push ghcr.io/pkb/neuro-base:latest
```

После публикации базовый образ доступен всей команде:
```bash
docker pull ghcr.io/pkb/neuro-base:latest
```

### 2. Конечный запуск — каждый разработчик у себя

Базовый образ + локальный код (через volume) + entrypoint:

```bash
# Просто запустить (образ уже есть в registry)
docker compose -f backend/service_checker/docker/docker-compose.yml up -d

# Пересобрать образ локально (если нет доступа к registry)
docker build -f backend/service_checker/docker/Dockerfile.base -t ghcr.io/pkb/neuro-base:latest .
docker compose -f backend/service_checker/docker/docker-compose.yml up -d
```

### Как это работает

```
┌─────────────────────────────────────────────────┐
│  ghcr.io/pkb/neuro-base (образ в registry)       │
│                                                   │
│  ┌───────────────────────────────────────────┐   │
│  │  Python 3.13 + pip-пакеты                 │   │
│  │  supervisor, libmagic1, libpq5            │   │
│  │  ENV: DB_HOST, REDIS_URL, MINIO_* и т.д.  │   │
│  └───────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
                        │
                        ▼ монтируется при запуске
┌─────────────────────────────────────────────────┐
│  ./backend/ (локальный код разработчика)          │
│                                                   │
│  ├── entrypoint.sh          → /app/backend/       │
│  ├── supervisord.conf       → (через volume)      │
│  ├── auth_service/          → (через volume)      │
│  ├── orchestrator_service/  → (через volume)      │
│  ├── registry_service/      → (через volume)      │
│  └── ...                                           │
└─────────────────────────────────────────────────┘
```

## Требования

- Docker Desktop 4.30+ (или Docker Engine 27+ с docker compose plugin)
- 4 CPU, 8 GB RAM (рекомендуется)
- Порты 5432, 6379, 9000, 9001, 8000, 8081-8087, 8090-8091 должны быть свободны

## Быстрый запуск

```bash
# 1. Собрать базовый образ (или pull из registry)
docker build -f backend/service_checker/docker/Dockerfile.base -t ghcr.io/pkb/neuro-base:latest .

# 2. Запустить всю инфраструктуру
docker compose -f backend/service_checker/docker/docker-compose.yml up -d

# 3. Проверить статус
docker compose -f backend/service_checker/docker/docker-compose.yml ps
docker compose -f backend/service_checker/docker/docker-compose.yml exec -T app supervisorctl status
```

## Переменные окружения

Все переменные заданы **по умолчанию** в `Dockerfile.base`.  
Для переопределения используйте `environment:` в `backend/service_checker/docker/docker-compose.yml`:

```yaml
app:
  environment:
    DATABASE_URL: postgresql+asyncpg://user:pass@host:5432/db
    JWT_SECRET_KEY: my-secret-key
    MOCK_LLM_ENABLED: "false"
```

## Проверка работоспособности

После запуска (~15–30 секунд на инициализацию):

```bash
# PostgreSQL
docker compose -f backend/service_checker/docker/docker-compose.yml exec -T postgres pg_isready -U pkb -d pkb_neuro

# Redis
docker compose -f backend/service_checker/docker/docker-compose.yml exec -T redis redis-cli ping

# MinIO
curl http://localhost:9000/minio/health/live

# Backend API (9 из 10 сервисов, registry упал — проблема кода)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/   # Orchestrator
curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/   # Auth
curl -s -o /dev/null -w "%{http_code}" http://localhost:8086/health  # Converter-Validator
curl -s -o /dev/null -w "%{http_code}" http://localhost:8087/health  # Parser

# Через service_checker
python backend/service_checker/service_checker.py docker --action health
```

## Управление

```bash
# Просмотр логов всех Python-процессов
docker compose -f backend/service_checker/docker/docker-compose.yml logs -f app

# Логи конкретного сервиса
docker compose -f backend/service_checker/docker/docker-compose.yml exec -T app tail -f /var/log/supervisor/orchestrator.log
docker compose -f backend/service_checker/docker/docker-compose.yml exec -T app tail -f /var/log/supervisor/rag_search.log
docker compose -f backend/service_checker/docker/docker-compose.yml exec -T app tail -f /var/log/supervisor/auth.log

# Остановка
docker compose -f backend/service_checker/docker/docker-compose.yml down

# Полный сброс (удалить volume с данными)
docker compose -f backend/service_checker/docker/docker-compose.yml down -v
```

## Публикация базового образа

```bash
# 1. Логин в registry
docker login ghcr.io -u USERNAME

# 2. Сборка базового образа
docker build -f backend/service_checker/docker/Dockerfile.base -t ghcr.io/pkb/neuro-base:latest .

# 3. Публикация
docker push ghcr.io/pkb/neuro-base:latest

# Также можно версионировать
docker build -f backend/service_checker/docker/Dockerfile.base -t ghcr.io/pkb/neuro-base:1.0.0 .
docker push ghcr.io/pkb/neuro-base:1.0.0
```

## Известные проблемы

### Registry Service (8084)
Падает с `ModuleNotFoundError: No module named 'api.v1.database'`.  
В файле `registry_service/api/v1/models/registry_service_enums.py` импорт `from ..database import Base`, но файл `database.py` отсутствует.  
**Требует фикса разработчиком.**

### Supervisorctl на Windows
Команда `docker compose -f backend/service_checker/docker/docker-compose.yml exec -T app supervisorctl status` может не работать в Git Bash из-за преобразования путей. Используйте PowerShell или:

```bash
# Через PowerShell
docker compose -f backend/service_checker/docker/docker-compose.yml exec -T app cat /var/log/supervisor/supervisord.log

# Или service_checker (fallback на чтение лога)
python backend/service_checker/service_checker.py docker --action health
```

## Альтернатива: полная сборка (Dockerfile.full)

Если нужно собрать монолитный образ со всем кодом (например, для деплоя):

```bash
docker build -f backend/service_checker/docker/Dockerfile.full -t pkb-neuro-full:latest .
docker run -d --name pkb-neuro pkb-neuro-full:latest
```

Старый `Dockerfile` переименован в `Dockerfile.full` и сохранён для обратной совместимости.
