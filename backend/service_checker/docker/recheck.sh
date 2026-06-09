#!/bin/bash
# =============================================================================
# PKB Neuroassistant — перезапуск контейнера + проверка
# =============================================================================
set -e

COMPOSE_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="$COMPOSE_DIR/docker-compose.yml"
SERVICE_CHECKER="$COMPOSE_DIR/../service_checker.py"

echo "1. Перезапуск контейнера..."
docker compose -f "$COMPOSE_FILE" restart app

echo ""
echo "2. Ожидание 10 секунд..."
sleep 10

echo ""
echo "3. Проверка + формирование отчётов (coverage)..."
python "$SERVICE_CHECKER" docker --action coverage

echo ""
echo "Отчёты сохранены в check_result/"
