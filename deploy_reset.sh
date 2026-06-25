#!/bin/bash
# =============================================================================
# PKB Neuroassistant — Deploy with Reset (git pull + clean + deploy)
#
# Обновление из git, полный сброс данных (удаление volumes БД и MinIO)
# и развёртывание всех сервисов с пересборкой.
# ВНИМАНИЕ: все данные (БД, объектное хранилище) будут удалены!
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${RED}============================================${NC}"
echo -e "${RED}  PKB Neuroassistant — Deploy with RESET${NC}"
echo -e "${RED}  WARNING: All data will be destroyed!${NC}"
echo -e "${RED}============================================${NC}"
echo ""

# ── Подтверждение ───────────────────────────────────────────────────────────
read -r -p "Are you sure you want to delete ALL data and redeploy? [y/N] " REPLY
if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi
echo ""

# ── 0. Проверка Docker ───────────────────────────────────────────────────────
echo -e "${YELLOW}[0/8] Checking Docker...${NC}"
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}ERROR: Docker is not running!${NC}"
    exit 1
fi
echo -e "  ${GREEN}Docker is running.${NC}"
echo ""

# ── 1. Git pull ──────────────────────────────────────────────────────────────
echo -e "${YELLOW}[1/8] Pulling latest code from git...${NC}"
git pull --ff-only
echo -e "  ${GREEN}Git updated.${NC}"
echo ""

# ── 2. Остановка + удаление volumes ─────────────────────────────────────────
echo -e "${YELLOW}[2/8] Stopping services and removing volumes...${NC}"
docker compose down -v
echo -e "  ${GREEN}Services stopped, volumes removed.${NC}"
echo ""

# ── 3. Подготовка TEI модели ─────────────────────────────────────────────────
echo -e "${YELLOW}[3/8] Preparing TEI model...${NC}"
PREPARE_SCRIPT="$SCRIPT_DIR/backend/diagnostics/prepare_tei_model.sh"
if [ -x "$PREPARE_SCRIPT" ]; then
    "$PREPARE_SCRIPT"
else
    echo -e "  ${YELLOW}prepare script not found at $PREPARE_SCRIPT${NC}"
fi
echo ""

# ── 4. Сборка и запуск ──────────────────────────────────────────────────────
echo -e "${YELLOW}[4/8] Building and starting all services...${NC}"
docker compose up -d --build
echo -e "  ${GREEN}All containers started.${NC}"
echo ""

# ── 5. Ожидание инициализации ───────────────────────────────────────────────
echo -e "${YELLOW}[5/8] Waiting for services to initialize (30s)...${NC}"
sleep 30
echo ""

# ── 6. Статус ────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[6/8] Service status:${NC}"
docker compose ps
echo ""

# ── 7. Health check ──────────────────────────────────────────────────────────
echo -e "${YELLOW}[7/8] Health check (Gateway):${NC}"
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:8080/health 2>/dev/null || echo "000")
if [ "$HEALTH" = "200" ]; then
    echo -e "  Gateway health: ${GREEN}$HEALTH OK${NC}"
else
    echo -e "  Gateway health: ${RED}$HEALTH${NC} (expected 200)"
fi
echo ""

# ── 8. Diagnostics server ─────────────────────────────────────────────────────
echo -e "${YELLOW}[8/8] Starting diagnostics server...${NC}"
DIAGNOSTICS_SCRIPT="$SCRIPT_DIR/backend/diagnostics/start_diagnostics_server.sh"
if [ -x "$DIAGNOSTICS_SCRIPT" ]; then
    "$DIAGNOSTICS_SCRIPT" start || echo -e "  ${YELLOW}(diagnostics server already running or port in use)${NC}"
else
    echo -e "  ${YELLOW}diagnostics script not found at $DIAGNOSTICS_SCRIPT${NC}"
fi
echo ""

echo -e "${GREEN}=== Deploy with reset complete ===${NC}"
echo ""
echo "  Backend API:     http://localhost:8080"
echo "  Web UI:          http://localhost:3300"
echo "  Diagnostics:     http://localhost:8080/api/v1/system/diagnostics"
echo ""
echo "  To view logs:    docker compose logs -f"
echo "  To stop:         docker compose down"
echo ""
