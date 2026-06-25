#!/bin/bash
# =============================================================================
# PKB Neuroassistant — Deploy (git pull + docker compose up)
#
# Обновление из git и развёртывание всех сервисов (корневой docker-compose.yml).
# Сохраняет существующие volumes (база данных, MinIO).
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Права на выполнение (git не всегда сохраняет chmod)
chmod +x deploy.sh deploy_reset.sh 2>/dev/null || true
chmod +x backend/diagnostics/*.sh backend/diagnostics/*.py 2>/dev/null || true

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  PKB Neuroassistant — Deploy${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# ── 0. Проверка Docker ───────────────────────────────────────────────────────
echo -e "${YELLOW}[0/6] Checking Docker...${NC}"
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}ERROR: Docker is not running!${NC}"
    exit 1
fi
echo -e "  ${GREEN}Docker is running.${NC}"
echo ""

# ── 1. Git pull ──────────────────────────────────────────────────────────────
echo -e "${YELLOW}[1/6] Pulling latest code from git...${NC}"
git pull --ff-only
echo -e "  ${GREEN}Git updated.${NC}"

# Восстановить права — git мог сбросить +x при обновлении файлов
chmod +x deploy.sh deploy_reset.sh 2>/dev/null || true
echo ""

# ── 2. Сборка и запуск ──────────────────────────────────────────────────────
echo -e "${YELLOW}[2/6] Building and starting all services...${NC}"
docker compose up -d --build
echo -e "  ${GREEN}All containers started.${NC}"
echo ""

# ── 3. Ожидание инициализации ───────────────────────────────────────────────
echo -e "${YELLOW}[3/6] Waiting for services to initialize (30s)...${NC}"
sleep 30
echo ""

# ── 4. Статус ────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[4/6] Service status:${NC}"
docker compose ps
echo ""

# ── 5. Health check ──────────────────────────────────────────────────────────
echo -e "${YELLOW}[5/6] Health check (Gateway):${NC}"
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:8080/health 2>/dev/null || echo "000")
if [ "$HEALTH" = "200" ]; then
    echo -e "  Gateway health: ${GREEN}$HEALTH OK${NC}"
else
    echo -e "  Gateway health: ${RED}$HEALTH${NC} (expected 200)"
fi
echo ""

# ── 6. Diagnostics server ─────────────────────────────────────────────────────
echo -e "${YELLOW}[6/6] Starting diagnostics server...${NC}"
DIAGNOSTICS_SCRIPT="$SCRIPT_DIR/backend/diagnostics/start_diagnostics_server.sh"
if [ -x "$DIAGNOSTICS_SCRIPT" ]; then
    "$DIAGNOSTICS_SCRIPT" start || echo -e "  ${YELLOW}(diagnostics server already running or port in use)${NC}"
else
    echo -e "  ${YELLOW}diagnostics script not found at $DIAGNOSTICS_SCRIPT${NC}"
fi
echo ""

echo -e "${GREEN}=== Deploy complete ===${NC}"
echo ""
echo "  Backend API:     http://localhost:8080"
echo "  Web UI:          http://localhost:3300"
echo "  Diagnostics:     http://localhost:8080/api/v1/system/diagnostics"
echo ""
echo "  To view logs:    docker compose logs -f"
echo "  To stop:         docker compose down"
echo ""
