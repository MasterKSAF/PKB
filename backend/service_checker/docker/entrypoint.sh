#!/bin/bash
# =============================================================================
# PKB Neuroassistant — Entrypoint
# Создаёт директории, ждёт БД и запускает supervisord
# =============================================================================
set -e

# Self-fix CRLF (Windows git clone converts LF to CRLF)
if grep -q $'\r$' "$0" 2>/dev/null; then
    echo "  ⚠ CRLF detected in entrypoint, fixing..."
    sed -i 's/\r$//' "$0"
    exec bash "$0" "$@"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║     PKB Neuroassistant — Backend Services                       ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# =============================================================================
# 1. Создание директорий для сервисов
# =============================================================================
echo "[1/3] Создание директорий..."
mkdir -p /app/backend/integration_service/files1 \
         /app/backend/integration_service/files2 \
         /app/backend/registry_service/files1 \
         /app/backend/registry_service/files2
echo "   ✓ Директории созданы"

# =============================================================================
# 2. Настройка PYTHONPATH
# =============================================================================
echo "[2/4] Настройка PYTHONPATH..."
export PYTHONPATH="/app/backend:/app/backend/shared:/app/backend/rag_builder_service/src:${PYTHONPATH:-}"
echo "   ✓ PYTHONPATH=$PYTHONPATH"

# =============================================================================
# 3. Автоустановка зависимостей (чтобы не ждать пересборки образа)
# =============================================================================
echo "[3/4] Проверка Python-зависимостей..."
if [ -f /app/backend/service_checker/docker/requirements.txt ]; then
    pip install --no-cache-dir -r /app/backend/service_checker/docker/requirements.txt 2>&1 | tail -1
    echo "   ✓ Зависимости актуальны"
else
    echo "   ⚠ requirements.txt не найден, пропускаем"
fi

# =============================================================================
# 4. Запуск supervisord
# =============================================================================
echo "[4/4] Запуск supervisord..."
echo ""

mkdir -p /var/log/supervisor /var/run/supervisor

if [ ! -f /etc/supervisor/conf.d/supervisord.conf ]; then
    echo "   ✗ /etc/supervisor/conf.d/supervisord.conf не найден!"
    exit 1
fi

echo "   Процессы под управлением:"
echo "   ┌──────────────────┬────────┬──────────────────────────┐"
echo "   │ Auth Service     │ 8082   │ Аутентификация           │"
echo "   │ Gateway          │ 8081   │ Mock-шлюз                │"
echo "   │ Orchestrator     │ 8000   │ Главное API              │"
echo "   │ Query            │ 8083   │ Чаты / сессии            │"
echo "   │ Registry         │ 8084   │ Классификаторы / реестр  │"
echo "   │ Integration      │ 8085   │ Внешние интеграции       │"
echo "   │ Converter-Valid  │ 8086   │ Валидация данных         │"
echo "   │ Parser           │ 8087   │ Парсинг документов       │"
echo "   │ OCR              │ 8088   │ OCR-распознавание        │"
echo "   │ RAG Builder      │ 8090   │ RAG-индексы              │"
echo "   │ RAG Search       │ 8091   │ Гибридный поиск          │"
echo "   └──────────────────┴────────┴──────────────────────────┘"
echo ""

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf -n
