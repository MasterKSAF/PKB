#!/bin/bash
# =============================================================================
# PKB Neuroassistant — re-check: clean DB + restart + full report
#
# Автоматически:
#   1. Проверяет наличие base-образа — если нет, собирает
#   2. Проверяет наличие модели TEI — если нет, скачивает
#   3. Проверяет, запущен ли контейнер TEI — если нет, запускает
#   4. Дропает схемы БД, сбрасывает Redis, перезапускает app
#   5. Запускает полный отчёт (health + coverage + pipeline)
#
# PostgreSQL и Redis не перезапускаются — только чистим данные.
# TEI контейнер не перезапускается (тяжёлая модель), только если не запущен.
# =============================================================================
set -e

COMPOSE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$COMPOSE_DIR"

echo "=== PKB Neuroassistant: Re-check ==="
echo ""

# ── 0. Создание .env ────────────────────────────────────────────────────
if ! python create_env.py; then
    echo "    WARNING: Failed to generate .env"
fi
echo ""

# ── 1. Проверка base-образа ────────────────────────────────────────────
IMAGE_NAME="ghcr.io/pkb/neuro-base:latest"
if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "$IMAGE_NAME"; then
    echo "[1/6] Base image found, skipping build."
else
    echo "[1/6] Base image not found — building..."
    echo ""
    DOCKER_SCOUT_SUPPRESS_ANALYSIS=1 docker build -f Dockerfile.base -t "$IMAGE_NAME" .
fi
echo ""

# ── 2. Проверка модели TEI ─────────────────────────────────────────────
if [ -f "tei_model/model.onnx" ]; then
    echo "[2/6] TEI model found, skipping download."
else
    echo "[2/6] TEI model not found — downloading..."
    echo ""
    python prepare_tei_model.py
fi
echo ""

# ── 3. Проверка контейнера TEI ─────────────────────────────────────────
echo "[3/6] Checking TEI container status..."
if docker compose ps --format "{{.State}}" tei 2>/dev/null | grep -q "running"; then
    echo "    TEI container is already running, skipping restart."
else
    echo "    TEI container is NOT running — starting..."
    docker compose up -d tei
    sleep 3
    if docker compose ps --format "{{.State}}" tei 2>/dev/null | grep -q "running"; then
        echo "    TEI container started."
    else
        echo "    WARNING: Failed to start TEI container, continuing anyway."
    fi
fi
echo ""

# ── 4. Очистка данных + перезапуск app ─────────────────────────────────
echo "[4/6] Dropping data + restarting app..."

echo "    Recreating database..."
docker exec pkb-postgres psql -U pkb -d postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE datname = 'pkb_neuro_check' AND pid <> pg_backend_pid();" 2>/dev/null || true
docker exec pkb-postgres psql -U pkb -d postgres -c "DROP DATABASE IF EXISTS pkb_neuro_check;" 2>/dev/null || true
docker exec pkb-postgres psql -U pkb -d postgres -c "CREATE DATABASE pkb_neuro_check;" 2>/dev/null || true

echo "    Flushing Redis..."
docker exec pkb-redis redis-cli FLUSHALL 2>/dev/null || echo "    (Redis not reachable, skipping)"

docker compose kill app 2>/dev/null || true
docker compose rm -f -v app 2>/dev/null || true
echo ""

# ── 5. Запуск app + отчёт ──────────────────────────────────────────────
echo "[5/6] Starting app..."
docker compose up -d app
echo "    App started. Running full report..."
echo ""

cd "$COMPOSE_DIR/../.."

echo "    Waiting for supervisor..."
until docker exec pkb-neuro supervisorctl status 2>/dev/null | grep -q "RUNNING"; do
    sleep 2
done

echo "    Patching RAG Builder tables..."
python -m service_checker docker --action patch-rag || true

echo "    Restarting RAG Builder with proper tables..."
docker exec pkb-neuro supervisorctl restart rag-builder 2>/dev/null || true

echo ""
echo "    Running full report..."
python -m service_checker docker --action full-report || echo "    WARNING: Some checks failed, check the report above."

echo ""
echo "=== Done ==="
echo "Reports: check_result/"
echo ""
