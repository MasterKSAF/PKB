#!/bin/bash
# =============================================================================
# PKB Neuroassistant — Entrypoint
# Создаёт директории, ждёт БД и запускает supervisord
# =============================================================================
set -e

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
echo "[2/3] Настройка PYTHONPATH..."
export PYTHONPATH="/app/backend:/app/backend/shared:/app/backend/rag_builder_service/src:${PYTHONPATH:-}"
echo "   ✓ PYTHONPATH=$PYTHONPATH"

# =============================================================================
# 3. Запуск supervisord
# =============================================================================
echo "[3/3] Запуск supervisord..."
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
echo "   │ RAG Builder      │ 8090   │ RAG-индексы              │"
echo "   │ RAG Search       │ 8091   │ Гибридный поиск          │"
echo "   └──────────────────┴────────┴──────────────────────────┘"
echo ""

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf -n
