#!/bin/bash
# =============================================================================
# PKB Neuroassistant — Entrypoint (SPK-версия)
# Для rag_builder_service_spd: создаёт .env для rag_builder_service_spd вместо
# rag_builder_service + rag_search_service
# =============================================================================
set -e

# Self-fix CRLF
if grep -q $'\r$' "$0" 2>/dev/null; then
    echo "  ⚠ CRLF detected in entrypoint, fixing..."
    sed -i 's/\r$//' "$0"
    exec bash "$0" "$@"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║     PKB Neuroassistant — SPD Backend Services                   ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# =============================================================================
# 1. Создание директорий для сервисов
# =============================================================================
echo "[1/6] Создание директорий..."
mkdir -p /app/backend/integration_service/files1 \
         /app/backend/integration_service/files2 \
         /app/backend/registry_service/files1 \
         /app/backend/registry_service/files2
echo "   ✓ Директории созданы"

# =============================================================================
# 2. Настройка PYTHONPATH
# =============================================================================
echo "[2/6] Настройка PYTHONPATH..."
export PYTHONPATH="/app/backend:/app/backend/shared:/app/backend/rag_builder_service_spd/src:${PYTHONPATH:-}"
echo "   ✓ PYTHONPATH=$PYTHONPATH"

# =============================================================================
# 3. Перезапись .env файлов сервисов
# =============================================================================
echo "[3/6] Перезапись .env файлов сервисов..."

# Registry .env (старый формат)
reg_env="/app/backend/registry_service/.env"
mkdir -p "$(dirname "$reg_env")"
cat > "$reg_env" <<-EOF
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_USERNAME=$DB_USERNAME
DB_PASSWORD=$DB_PASSWORD
DB_DATABASE=$DB_DATABASE
DATABASE_URL=$DATABASE_URL
EMBEDDING_API_KEY=$EMBEDDING_API_KEY
EMBEDDING_API_URL=$EMBEDDING_BASE_URL
EMBEDDING_MODEL=$EMBEDDING_MODEL
EMBEDDING_DIM=$EMBEDDING_DIM
EMBEDDING_PROVIDER=$EMBEDDING_PROVIDER
VECTOR_DIMENSION=$EMBEDDING_DIM
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_SECRET=$JWT_SECRET_KEY
JWT_ALGORITHM=$JWT_ALGORITHM
EOF
echo "   ✓ $reg_env"

# rag_builder_service_spd .env (формат Settings из config.py)
spd_env="/app/backend/rag_builder_service_spd/.env"
mkdir -p "$(dirname "$spd_env")"
cat > "$spd_env" <<-EOF
POSTGRES_HOST=$DB_HOST
POSTGRES_PORT=$DB_PORT
POSTGRES_DB=$DB_DATABASE
POSTGRES_USER=$DB_USERNAME
POSTGRES_PASSWORD=$DB_PASSWORD
EMBEDDING_PROVIDER=$EMBEDDING_PROVIDER
EMBEDDING_MODEL=$EMBEDDING_MODEL
EMBEDDING_DIM=$EMBEDDING_DIM
EMBEDDING_API_KEY=$EMBEDDING_API_KEY
EMBEDDING_API_BASE_URL=$EMBEDDING_BASE_URL
EOF
echo "   ✓ $spd_env"
# Auth service
auth_env="/app/backend/auth_service/.env"
mkdir -p "$(dirname "$auth_env")"
if [ -n "${JWT_SECRET_KEY:-}" ]; then
    cat > "$auth_env" <<-EOF
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ALGORITHM=$JWT_ALGORITHM
EOF
    echo "   ✓ $auth_env (JWT_SECRET_KEY, JWT_ALGORITHM)"
fi
echo "   ✓ .env файлы обновлены"

# =============================================================================
# 4. Автоустановка Python-зависимостей
# =============================================================================
echo "[4/6] Проверка Python-зависимостей..."
if [ -f /app/backend/service_checker/docker/requirements.txt ]; then
    pip install --no-cache-dir -r /app/backend/service_checker/docker/requirements.txt 2>&1 | tail -1
    echo "   ✓ Python-зависимости актуальны"
else
    echo "   ⚠ requirements.txt не найден, пропускаем"
fi

# =============================================================================
# 5. Инициализация БД
# =============================================================================
echo "[5/6] Инициализация БД..."
SETUP_DB="/app/backend/service_checker/core/setup_db.py"
if [ -f "$SETUP_DB" ]; then
    python "$SETUP_DB" --docker 2>&1 || {
        echo "   ⚠ setup_db.py завершился с ошибкой (код $?)"
        echo "   ⚠ Сервисы будут запущены, но БД может быть не готова"
    }
    echo "   ✓ БД инициализирована"
else
    echo "   ⚠ setup_db.py не найден, пропускаем инициализацию БД"
fi

# =============================================================================
# 6. Инициализация MinIO bucket'ов
# =============================================================================
echo "[6/7] Инициализация MinIO bucket'ов..."
python /app/backend/service_checker/docker/init_minio.py 2>&1 || {
    echo "   ⚠ Не удалось создать bucket'ы MinIO"
}

echo ""

# =============================================================================
# 7. Запуск supervisord
# =============================================================================
echo "[7/7] Запуск supervisord..."
echo ""

mkdir -p /var/log/supervisor /var/run/supervisor

ln -sf /etc/supervisor/conf.d/supervisord.conf /etc/supervisor/supervisord.conf 2>/dev/null || true

if [ ! -f /etc/supervisor/conf.d/supervisord.conf ]; then
    echo "   ✗ /etc/supervisor/conf.d/supervisord.conf не найден!"
    exit 1
fi

echo ""
echo "   Процессы под управлением:"
echo "   ┌──────────────────┬────────┬──────────────────────────┐"
echo "   │ Auth Service     │ 8082   │ Аутентификация           │"
echo "   │ Gateway          │ 8080   │ Mock-шлюз                │"
echo "   │ Orchestrator     │ 8081   │ Главное API              │"
echo "   │ Query            │ 8083   │ Чаты / сессии            │"
echo "   │ Registry         │ 8084   │ Классификаторы / реестр  │"
echo "   │ Integration      │ 8085   │ Внешние интеграции       │"
echo "   │ Converter-Valid  │ 8086   │ Валидация данных         │"
echo "   │ Parser           │ 8087   │ Парсинг документов       │"
echo "   │ OCR              │ 8088   │ OCR-распознавание        │"
echo "   │ RAG Builder SPD  │ 8090   │ RAG-индексы + поиск v2   │"
echo "   └──────────────────┴────────┴──────────────────────────┘"
echo ""

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf -n
