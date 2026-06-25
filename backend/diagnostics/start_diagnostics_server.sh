#!/bin/bash
# =============================================================================
# PKB Neuroassistant — Diagnostics Server (start/stop/status)
#
# Управление HTTP-сервером диагностики (порт 9090).
# Позволяет получать server_diagnostics.sh удалённо по HTTP.
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="/tmp/pkb-diagnostics-server.pid"
PORT="${DIAGNOSTICS_PORT:-9090}"

# Определяем интерпретатор Python
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done
if [ -z "$PYTHON" ]; then
    echo "ERROR: Python not found (tried python3, python)"
    exit 1
fi

# Проверка свободен ли порт
check_port() {
    if ss -tlnp "sport = :$PORT" 2>/dev/null | grep -q ":$PORT"; then
        return 1
    fi
    return 0
}

case "${1:-start}" in
    start)
        # Проверка по PID-файлу
        if [ -f "$PID_FILE" ]; then
            OLD_PID=$(cat "$PID_FILE")
            if kill -0 "$OLD_PID" 2>/dev/null; then
                echo "Diagnostics server already running (PID $OLD_PID) on port $PORT."
                echo "  -> curl http://localhost:$PORT/diagnostics"
                exit 0
            else
                rm -f "$PID_FILE"
            fi
        fi

        # Проверка порта
        if ! check_port; then
            echo "ERROR: Port $PORT is already in use."
            exit 1
        fi

        echo "Starting diagnostics server on port $PORT..."
        nohup "$PYTHON" "$SCRIPT_DIR/diagnostics_server.py" "$PORT" \
            > /dev/null 2>&1 &
        PID=$!
        echo $PID > "$PID_FILE"
        sleep 1

        if kill -0 "$PID" 2>/dev/null; then
            echo "Diagnostics server started (PID $PID)."
            echo "  -> curl http://localhost:$PORT/diagnostics"
        else
            echo "ERROR: Failed to start diagnostics server."
            rm -f "$PID_FILE"
            exit 1
        fi
        ;;
    stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            kill "$PID" 2>/dev/null || true
            rm -f "$PID_FILE"
            echo "Diagnostics server stopped."
        else
            echo "Diagnostics server not running."
        fi
        ;;
    status)
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo "Diagnostics server is running (PID $(cat "$PID_FILE")) on port $PORT."
        else
            echo "Diagnostics server is not running."
            [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
        fi
        ;;
    restart)
        "$0" stop
        sleep 1
        "$0" start
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac
