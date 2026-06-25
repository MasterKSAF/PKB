#!/bin/bash
# =============================================================================
# PKB Neuroassistant — Deploy with Reset (clean + deploy)
#
# Полный сброс данных (удаление volumes БД и MinIO) и развёртывание.
# ВНИМАНИЕ: все данные (БД, объектное хранилище) будут удалены!
#
# Останавливает сервисы, чистит volumes, затем вызывает deploy.sh.
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Права на выполнение (git мог сбросить +x)
chmod +x deploy.sh deploy_reset.sh 2>/dev/null || true

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

# ── 1. Остановка сервисов ────────────────────────────────────────────────────
echo -e "${YELLOW}[1/3] Stopping services...${NC}"
docker compose down
echo ""

# ── 2. Удаление volumes (huggingface_cache — кеш Infinity — оставляем) ───────
echo -e "${YELLOW}[2/3] Removing data volumes (pg_data, minio_data)...${NC}"
docker volume rm \
  $(docker volume ls --filter label=com.docker.compose.volume=pg_data -q) \
  $(docker volume ls --filter label=com.docker.compose.volume=minio_data -q) \
  2>/dev/null || true
echo -e "  ${GREEN}Data volumes removed.${NC}"
echo ""

# ── 3. Вызов deploy.sh ────────────────────────────────────────────────────────
echo -e "${YELLOW}[3/3] Running deploy.sh...${NC}"
echo ""
exec "$SCRIPT_DIR/deploy.sh"
