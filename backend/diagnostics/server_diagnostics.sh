#!/bin/bash
# =============================================================================
# PKB Neuroassistant — Server Diagnostics
#
# Диагностика состояния сервера: размещение, git, Docker, сервисы.
#
# Usage:
#   ./server_diagnostics.sh                    # базовая сводка
#   ./server_diagnostics.sh --summary           # то же
#   ./server_diagnostics.sh --service <name>    # диагностика конкретного сервиса
#   ./server_diagnostics.sh --verbose           # расширенная (с системными логами)
#   ./server_diagnostics.sh --logs 100          # количество строк логов (по умолч. 20)
#   ./server_diagnostics.sh --service parser --verbose --logs 50  # комбинированный
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m'

COMPOSE_PROJECT="pkb"

# =============================================================================
# Helper
# =============================================================================

header() {
    echo -e "${CYAN}====================================================${NC}"
    echo -e "${CYAN}   $1${NC}"
    echo -e "${CYAN}====================================================${NC}"
    echo ""
}

section() {
    echo -e "${YELLOW}[$1] $2${NC}"
}

# =============================================================================
# Функции-блоки
# =============================================================================

system_info() {
    section "1" "System resources"
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
}

disk_usage() {
    section "2" "Disk usage"
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
}

docker_df() {
    section "3" "Docker disk usage"
    docker system df 2>/dev/null || echo "  (unable to query)"
    echo ""
}

git_status() {
    section "4" "Git status"
    if git rev-parse --git-dir >/dev/null 2>&1; then
        BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "detached")
        echo "  Branch:     $BRANCH"
        echo "  Commit:     $(git rev-parse --short HEAD 2>/dev/null)"
        echo "  Message:    $(git log -1 --pretty=%s 2>/dev/null)"

        if git diff --quiet 2>/dev/null; then
            echo -e "  Working dir: ${GREEN}clean${NC}"
        else
            echo -e "  Working dir: ${RED}modified${NC} $(git diff --stat 2>/dev/null | tail -1)"
        fi

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

        echo ""
        echo "  Last commits:"
        git log --oneline -5 2>/dev/null | sed 's/^/    /'
    else
        echo -e "  ${RED}Not a git repository${NC}"
    fi
    echo ""
}

docker_containers() {
    section "5" "Docker containers"

    TOTAL=$(docker ps -a --filter "label=com.docker.compose.project=$COMPOSE_PROJECT" -q 2>/dev/null | wc -l)
    RUNNING=$(docker ps --filter "label=com.docker.compose.project=$COMPOSE_PROJECT" -q 2>/dev/null | wc -l)
    if [ "$TOTAL" -gt 0 ]; then
        echo -e "  Running: ${GREEN}$RUNNING${NC} / $TOTAL total"
    else
        echo -e "  ${RED}No project containers found${NC}"
    fi
    echo ""

    ALL_CONTAINERS=$(docker ps -a --filter "label=com.docker.compose.project=$COMPOSE_PROJECT" \
      --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null)
    if [ -n "$ALL_CONTAINERS" ]; then
        echo "$ALL_CONTAINERS"
    else
        ALL_CONTAINERS=$(docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | grep -E "^pkb-" || true)
        if [ -n "$ALL_CONTAINERS" ]; then
            echo "$ALL_CONTAINERS"
        fi
    fi
    echo ""
}

docker_compose_ps() {
    section "6" "Docker Compose services"
    if [ -f docker-compose.yml ]; then
        docker compose ps 2>/dev/null || echo "  (compose project not running)"
    else
        echo "  docker-compose.yml not found"
    fi
    echo ""
}

health_checks() {
    section "7" "Health checks"

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:8080/health 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "  Gateway  http://localhost:8080/health   ${GREEN}${HTTP_CODE} OK${NC}"
    else
        echo -e "  Gateway  http://localhost:8080/health   ${RED}${HTTP_CODE}${NC}"
    fi

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:3300 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
        echo -e "  Web UI   http://localhost:3300           ${GREEN}${HTTP_CODE} OK${NC}"
    else
        echo -e "  Web UI   http://localhost:3300           ${RED}${HTTP_CODE}${NC}"
    fi

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
}

ports_info() {
    section "8" "Ports"
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
}

volumes_info() {
    section "9" "Volumes (${COMPOSE_PROJECT})"
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
}

logs_errors() {
    local log_lines=${1:-20}
    section "10" "Recent errors in logs (last $log_lines lines per service)"
    if [ -f docker-compose.yml ]; then
        SERVICES=$(docker compose config --services 2>/dev/null)
        local found_errors=false
        if [ -n "$SERVICES" ]; then
            for svc in $SERVICES; do
                ERRORS=$(docker compose logs --tail=100 "$svc" 2>/dev/null | grep -iE "error|traceback|exception|fail|critical" | tail -"$log_lines" || true)
                if [ -n "$ERRORS" ]; then
                    found_errors=true
                    echo -e "  ${RED}$svc${NC}"
                    echo "$ERRORS" | sed 's/^/    /'
                    echo ""
                fi
            done
            if [ "$found_errors" = false ]; then
                echo "  (no errors found)"
            fi
        else
            echo "  (no services defined)"
        fi
    else
        echo "  (docker-compose.yml not found)"
    fi
    echo ""
}

summary_end() {
    echo -e "${GREEN}====================================================${NC}"
    echo -e "${GREEN}   Summary complete${NC}"
    echo -e "${GREEN}====================================================${NC}"
}

# =============================================================================
# Диагностика одного сервиса
# =============================================================================

service_diagnostics() {
    local svc_name="$1"
    local log_lines="${2:-20}"

    # Определяем container_name по имени сервиса
    local container="pkb-${svc_name}"

    header "Service diagnostics: $svc_name ($container)"

    # Docker inspect
    section "1" "Container info"
    docker inspect "$container" --format '
  Name:       {{.Name}}
  Image:      {{.Config.Image}}
  Status:     {{.State.Status}}
  Health:     {{.State.Health.Status}}
  Created:    {{.Created}}
  Ports:      {{range $p,$v := .NetworkSettings.Ports}}{{$p}} {{end}}
  IP:         {{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}
' 2>/dev/null || echo -e "  ${RED}Container $container not found${NC}"
    echo ""

    # Health check
    section "2" "Health check"
    local port=""
    port=$(docker inspect "$container" --format '{{range $p,$v := .NetworkSettings.Ports}}{{$p}}{{end}}' 2>/dev/null | grep -oE '[0-9]+' | head -1)
    if [ -n "$port" ]; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "http://localhost:$port/health" 2>/dev/null || echo "000")
        echo -e "  http://localhost:$port/health → ${HTTP_CODE}"
    else
        echo "  (no host port mapped)"
    fi
    echo ""

    # Resource usage
    section "3" "Resource usage"
    docker stats "$container" --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}" 2>/dev/null || echo "  (unable to get stats)"
    echo ""

    # Logs (errors)
    section "4" "Errors in logs (last $log_lines lines)"
    local errors
    errors=$(docker logs "$container" --tail 100 2>&1 | grep -iE "error|traceback|exception|fail|critical" | tail -"$log_lines" || true)
    if [ -n "$errors" ]; then
        echo "$errors" | sed 's/^/  /'
    else
        echo "  (no errors found)"
    fi
    echo ""

    # Recent logs
    section "5" "Recent logs (last $log_lines lines)"
    docker logs "$container" --tail "$log_lines" 2>&1 | sed 's/^/  /' || echo "  (unable to get logs)"
    echo ""

    echo -e "${GREEN}====================================================${NC}"
    echo -e "${GREEN}   Service diagnostics complete: $svc_name${NC}"
    echo -e "${GREEN}====================================================${NC}"
}

# =============================================================================
# Системные логи хоста
# =============================================================================

system_logs() {
    local log_lines="${1:-50}"

    header "System logs"

    # Kernel messages
    section "1" "Kernel (dmesg) — last $log_lines lines"
    if command -v dmesg &>/dev/null; then
        dmesg --level=err,warn 2>/dev/null | tail -"$log_lines" | sed 's/^/  /' || echo "  (unable to read dmesg)"
    else
        echo "  (dmesg not available)"
    fi
    echo ""

    # Journalctl
    section "2" "System journal (journalctl) — last $log_lines lines"
    if command -v journalctl &>/dev/null; then
        journalctl -n "$log_lines" --no-pager 2>/dev/null | grep -iE "error|fail|critical|oom|killed" | sed 's/^/  /' || echo "  (no matching entries)"
        echo ""
        journalctl -n "$log_lines" --no-pager 2>/dev/null | tail -5 | sed 's/^/  [recent] /'
    else
        echo "  (journalctl not available)"
    fi
    echo ""

    # System memory pressure
    section "3" "Memory pressure"
    if [ -f /proc/pressure/memory ]; then
        cat /proc/pressure/memory | sed 's/^/  /'
    else
        echo "  (not available)"
    fi
    echo ""

    # Load average detail
    section "4" "CPU load detail"
    cat /proc/loadavg | awk '{printf "  1min: %s  5min: %s  15min: %s  procs: %s\n", $1, $2, $3, $4}'
    echo ""

    echo -e "${GREEN}====================================================${NC}"
    echo -e "${GREEN}   System logs complete${NC}"
    echo -e "${GREEN}====================================================${NC}"
}

# =============================================================================
# Summary — краткая сводка
# =============================================================================

summary() {
    local log_lines="${1:-20}"
    local verbose="${2:-false}"

    header "PKB Neuroassistant — Server Diagnostics (summary)"

    system_info
    disk_usage
    git_status
    docker_containers
    docker_compose_ps
    health_checks
    ports_info
    volumes_info
    logs_errors "$log_lines"

    if [ "$verbose" = "true" ]; then
        system_logs 50
    fi

    summary_end
}

# =============================================================================
# Разбор аргументов
# =============================================================================

SUMMARY_MODE=false
VERBOSE=false
SERVICE=""
LOGS=20

while [[ $# -gt 0 ]]; do
    case $1 in
        --summary)
            SUMMARY_MODE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --service)
            SERVICE="$2"
            shift 2
            ;;
        --logs)
            LOGS="${2:-20}"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --summary           Базовая сводка (по умолчанию)"
            echo "  --service <name>    Диагностика конкретного сервиса (gateway, parser, ...)"
            echo "  --verbose           Расширенный вывод (системные логи)"
            echo "  --logs <N>          Количество строк логов (по умолч. 20)"
            echo "  --help, -h          Показать справку"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--summary] [--service <name>] [--verbose] [--logs N]"
            exit 1
            ;;
    esac
done

# По умолчанию — summary
if [ "$SUMMARY_MODE" = false ] && [ -z "$SERVICE" ]; then
    SUMMARY_MODE=true
fi

# -----------------------------------------------------------------------------
# Выполнение
# -----------------------------------------------------------------------------

if [ "$SUMMARY_MODE" = true ]; then
    summary "$LOGS" "$VERBOSE"
fi

if [ -n "$SERVICE" ]; then
    service_diagnostics "$SERVICE" "$LOGS"
    if [ "$VERBOSE" = true ]; then
        system_logs 50
    fi
fi

if [ "$SUMMARY_MODE" = false ] && [ -z "$SERVICE" ] && [ "$VERBOSE" = true ]; then
    # Только verbose (без summary/service)
    system_logs 50
fi
