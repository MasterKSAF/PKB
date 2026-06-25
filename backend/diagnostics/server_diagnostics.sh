#!/bin/bash
# =============================================================================
# PKB Neuroassistant — Server Diagnostics
#
# Диагностика состояния сервера: размещение, git, Docker, сервисы.
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Поднимаемся к корню проекта (где лежит docker-compose.yml)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m'

echo -e "${CYAN}====================================================${NC}"
echo -e "${CYAN}   PKB Neuroassistant — Server Diagnostics${NC}"
echo -e "${CYAN}====================================================${NC}"
echo ""

# ── 1. Система ───────────────────────────────────────────────────────────────
echo -e "${YELLOW}[1] System resources${NC}"
echo "  Hostname:  $(hostname)"
echo "  Uptime:    $(uptime -p 2>/dev/null || uptime)"
echo "  Load:      $(uptime | awk -F'load average:' '{print $2}' | xargs)"
echo "  CPU:       $(nproc) cores"
MEM_TOTAL=$(free -h | awk '/^Mem:/ {print $2}')
MEM_USED=$(free -h | awk '/^Mem:/ {print $3}')
MEM_AVAIL=$(free -h | awk '/^Mem:/ {print $7}')
echo "  Memory:    ${MEM_USED} / ${MEM_TOTAL}  (avail: ${MEM_AVAIL})"
echo "  Swap:      $(free -h | awk '/^Swap:/ {print $3 " / " $2}')"
echo ""

# ── 2. Диски (размещение) ────────────────────────────────────────────────────
echo -e "${YELLOW}[2] Disk usage${NC}"
df -h / /var/lib/docker 2>/dev/null | awk '
  NR==1 {print "  " $0}
  NR>1  {printf "  %-20s %8s %8s %5s %s\n", $6, $3, $4, $5, $1}'
echo ""

PROJECT_SIZE=$(du -sh . 2>/dev/null | cut -f1)
echo "  Project size: $PROJECT_SIZE ($(find . -type f | wc -l) files)"
echo ""

DOCKER_ROOT=$(docker info 2>/dev/null | awk -F': ' '/Docker Root Dir/ {print $2}')
if [ -n "$DOCKER_ROOT" ]; then
    DOCKER_DISK=$(df -h "$DOCKER_ROOT" 2>/dev/null | awk 'NR==2 {print $3 " / " $2 " (" $5 ")"}')
    echo "  Docker root: $DOCKER_ROOT ($DOCKER_DISK)"
fi
echo ""

# ── 3. Docker system (место) ────────────────────────────────────────────────
echo -e "${YELLOW}[3] Docker disk usage${NC}"
docker system df 2>/dev/null || echo "  (unable to query)"
echo ""

# ── 4. Git (обновление) ─────────────────────────────────────────────────────
echo -e "${YELLOW}[4] Git status${NC}"
if git rev-parse --git-dir >/dev/null 2>&1; then
    BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "detached")
    echo "  Branch:     $BRANCH"
    echo "  Commit:     $(git rev-parse --short HEAD 2>/dev/null)"
    echo "  Message:    $(git log -1 --pretty=%s 2>/dev/null)"

    # Статус рабочей директории
    if git diff --quiet 2>/dev/null; then
        echo -e "  Working dir: ${GREEN}clean${NC}"
    else
        echo -e "  Working dir: ${RED}modified${NC} $(git diff --stat 2>/dev/null | tail -1)"
    fi

    # Отставание/опережение от origin
    UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name "@{upstream}" 2>/dev/null || true)
    if [ -n "$UPSTREAM" ]; then
        BEHIND=$(git rev-list --count "HEAD..@{upstream}" 2>/dev/null || echo 0)
        AHEAD=$(git rev-list --count "@{upstream}..HEAD" 2>/dev/null || echo 0)
        if [ "$BEHIND" -gt 0 ] || [ "$AHEAD" -gt 0 ]; then
            echo "  Upstream:   $(echo "$UPSTREAM" | sed 's|refs/remotes/||')  (ahead $AHEAD, behind $BEHIND)"
        else
            echo "  Upstream:   $(echo "$UPSTREAM" | sed 's|refs/remotes/||')  ${GREEN}up to date${NC}"
        fi
    fi

    # Последние коммиты
    echo ""
    echo "  Last commits:"
    git log --oneline -5 2>/dev/null | sed 's/^/    /'
else
    echo -e "  ${RED}Not a git repository${NC}"
fi
echo ""

# ── 5. Docker контейнеры ────────────────────────────────────────────────────
echo -e "${YELLOW}[5] Docker containers${NC}"

COMPOSE_PROJECT="pkb"

# Сводка: сколько запущено из скольких
TOTAL=$(docker ps -a --filter "label=com.docker.compose.project=$COMPOSE_PROJECT" -q 2>/dev/null | wc -l)
RUNNING=$(docker ps --filter "label=com.docker.compose.project=$COMPOSE_PROJECT" -q 2>/dev/null | wc -l)
if [ "$TOTAL" -gt 0 ]; then
    echo -e "  Running: ${GREEN}$RUNNING${NC} / $TOTAL total"
else
    echo -e "  ${RED}No project containers found${NC}"
fi
echo ""

# Все контейнеры проекта (не только running)
ALL_CONTAINERS=$(docker ps -a --filter "label=com.docker.compose.project=$COMPOSE_PROJECT" \
  --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null)
if [ -n "$ALL_CONTAINERS" ]; then
    echo "$ALL_CONTAINERS"
else
    # fallback: ищем контейнеры с префиксом pkb-
    ALL_CONTAINERS=$(docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | grep -E "^pkb-" || true)
    if [ -n "$ALL_CONTAINERS" ]; then
        echo "$ALL_CONTAINERS"
    fi
fi
echo ""

# ── 6. Docker Compose статус ────────────────────────────────────────────────
echo -e "${YELLOW}[6] Docker Compose services${NC}"
if [ -f docker-compose.yml ]; then
    docker compose ps 2>/dev/null || echo "  (compose project not running)"
else
    echo "  docker-compose.yml not found"
fi
echo ""

# ── 7. Health checks ─────────────────────────────────────────────────────────
echo -e "${YELLOW}[7] Health checks${NC}"

# Gateway — единая точка входа
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:8080/health 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "  Gateway  http://localhost:8080/health   ${GREEN}${HTTP_CODE} OK${NC}"
else
    echo -e "  Gateway  http://localhost:8080/health   ${RED}${HTTP_CODE}${NC}"
fi

# Web UI
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:3300 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo -e "  Web UI   http://localhost:3300           ${GREEN}${HTTP_CODE} OK${NC}"
else
    echo -e "  Web UI   http://localhost:3300           ${RED}${HTTP_CODE}${NC}"
fi

# Docker healthcheck всех сервисов (инфраструктура + backend)
HEALTH_SERVICES="pkb-postgres pkb-redis pkb-minio pkb-tei pkb-auth pkb-registry pkb-parser pkb-converter-validator pkb-rag-builder pkb-rag-search pkb-query pkb-orchestrator pkb-gateway"
for container in $HEALTH_SERVICES; do
    STATUS=$(docker inspect "$container" --format '{{.State.Health.Status}}' 2>/dev/null || echo "not found")
    NAME=$(echo "$container" | sed 's/^pkb-//')
    case "$STATUS" in
        healthy)   echo -e "  $NAME  ${GREEN}healthy${NC}" ;;
        starting)  echo -e "  $NAME  ${YELLOW}starting${NC}" ;;
        unhealthy) echo -e "  $NAME  ${RED}unhealthy${NC}" ;;
        *)         echo -e "  $NAME  ${RED}${STATUS}${NC}" ;;
    esac
done
echo ""

# ── 8. Порты ─────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[8] Ports${NC}"
PORTS=(8080 3300 8082 8081 8083 8084 8086 8087 8090 8091 15432 16379 19001 18092)
for PORT in "${PORTS[@]}"; do
    if ss -tlnp "sport = :$PORT" 2>/dev/null | grep -q ":$PORT"; then
        PROC=$(ss -tlnp "sport = :$PORT" 2>/dev/null | sed -n 's/.*users:(("\([^"]*\)".*/\1/p' | head -1)
        echo -e "  $PORT  ${GREEN}in use${NC}  ($PROC)"
    else
        echo -e "  $PORT  ${YELLOW}free${NC}"
    fi
done
echo ""

# ── 9. Docker volumes ────────────────────────────────────────────────────────
echo -e "${YELLOW}[9] Volumes (${COMPOSE_PROJECT})${NC}"
VOLUMES=$(docker volume ls --filter "label=com.docker.compose.project=$COMPOSE_PROJECT" --format "{{.Name}}" 2>/dev/null)
if [ -n "$VOLUMES" ]; then
    while IFS= read -r vol; do
        SIZE=$(docker system df -v 2>/dev/null | grep "$vol" | awk '{print $3}' || echo "?")
        echo "  $vol  (${SIZE})"
    done <<< "$VOLUMES"
else
    echo "  No volumes found."
fi
echo ""

# ── 10. Logs (ошибки) ────────────────────────────────────────────────────────
echo -e "${YELLOW}[10] Recent errors in logs (last 20 lines per service)${NC}"
if [ -f docker-compose.yml ]; then
    SERVICES=$(docker compose config --services 2>/dev/null)
    if [ -n "$SERVICES" ]; then
        for svc in $SERVICES; do
            ERRORS=$(docker compose logs --tail=100 "$svc" 2>/dev/null | grep -iE "error|traceback|exception|fail|critical" | tail -20 || true)
            if [ -n "$ERRORS" ]; then
                echo -e "  ${RED}$svc${NC}"
                echo "$ERRORS" | sed 's/^/    /'
                echo ""
            fi
        done
        echo "  (no errors found)"
    else
        echo "  (no services defined)"
    fi
else
    echo "  (docker-compose.yml not found)"
fi
echo ""

echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}   Diagnostics complete${NC}"
echo -e "${GREEN}====================================================${NC}"
