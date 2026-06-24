#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Диагностика сервисов: проверка URL, портов и проксирования
# ============================================================

HOST="${1:-195.70.195.203}"
GATEWAY_PORT="${2:-8080}"
BASE="http://${HOST}:${GATEWAY_PORT}"

PASS=0
FAIL=0

pass() { PASS=$((PASS+1)); echo "  ✅ $1"; }
fail() { FAIL=$((FAIL+1)); echo "  ❌ $1"; }

echo ""
echo "══════════════════════════════════════════════"
echo " Диагностика PKB Neuroassistant"
echo " Хост: $HOST:$GATEWAY_PORT"
echo " $(date)"
echo "══════════════════════════════════════════════"
echo ""

# --------------------------------------------
# 1. Gateway
# --------------------------------------------
echo "── 1. Gateway ────────────────────────────"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$BASE/system/health" 2>/dev/null || echo "000")
case "$STATUS" in
  200) pass "GET /system/health → $STATUS" ;;
  000) fail "Gateway недоступен: $BASE — ERR_CONNECTION_REFUSED. Запусти gateway: docker compose up -d gateway" ;;
  *)   fail "GET /system/health → $STATUS (ожидался 200)" ;;
esac

# Gateway mode
MODE=$(curl -s --connect-timeout 5 "$BASE/system/mode" 2>/dev/null || echo '{"mode":"error"}')
echo "      mode: $(echo "$MODE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('mode','unknown'))" 2>/dev/null || echo "unknown")"

# --------------------------------------------
# 2. Auth
# --------------------------------------------
echo ""
echo "── 2. Auth Service ───────────────────────"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$BASE/api/v1/health" 2>/dev/null || echo "000")
case "$STATUS" in
  200|401|403) pass "GET /api/v1/health → $STATUS (auth response, ожидаемо)" ;;
  404)         fail "GET /api/v1/health → 404. Gateway не нашёл маршрут → AUTH_SERVICE_URL" ;;
  502)         fail "GET /api/v1/health → 502. Gateway нашёл маршрут, но AUTH не отвечает (не запущен или порт не тот)" ;;
  000)         fail "Gateway недоступен" ;;
  *)           fail "GET /api/v1/health → $STATUS" ;;
esac

# Auth token endpoint
STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 \
  -X POST "$BASE/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test"}' 2>/dev/null || echo "000")
case "$STATUS" in
  200|422|400|401) pass "POST /api/v1/auth/token → $STATUS (endpoint работает)" ;;
  404)             fail "POST /api/v1/auth/token → 404. Нет маршрута. Проверь gateway → AUTH_SERVICE_URL" ;;
  502)             fail "POST /api/v1/auth/token → 502. AUTH не отвечает" ;;
  000)             fail "Gateway недоступен" ;;
  *)               fail "POST /api/v1/auth/token → $STATUS" ;;
esac

# --------------------------------------------
# 3. Registry
# --------------------------------------------
echo ""
echo "── 3. Registry ───────────────────────────"

# Просто health (если registry имеет /api/v1/health)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$BASE/api/v1/registry/documents?page=1&page_size=1" 2>/dev/null || echo "000")
case "$STATUS" in
  200|401|403|422) pass "GET /api/v1/registry/documents → $STATUS (route ok)" ;;
  404)             fail "GET /api/v1/registry/documents → 404. Gateway → REGISTRY трансформация не сработала" ;;
  502)             fail "GET /api/v1/registry/documents → 502. Registry не отвечает" ;;
  000)             fail "Gateway недоступен" ;;
  *)               fail "GET /api/v1/registry/documents → $STATUS" ;;
esac

# Проверка на дубль /api/v1/api/v1 в ответе (если 404 — это нормально)
BODY=$(curl -s --connect-timeout 5 "$BASE/api/v1/registry/documents?page=1&page_size=1" 2>/dev/null || echo "")
if echo "$BODY" | grep -q "api/v1/api/v1"; then
  fail "❗ Найден дубль /api/v1/api/v1 в ответе — REGISTRY_SERVICE_URL содержит /api/v1, а gateway добавляет его же"
fi

# --------------------------------------------
# 4. RAG Builder
# --------------------------------------------
echo ""
echo "── 4. RAG Builder ────────────────────────"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 \
  -X POST "$BASE/api/v1/rag/build" \
  -H "Content-Type: application/json" \
  -d '{"document_id":1,"sections":[]}' 2>/dev/null || echo "000")
case "$STATUS" in
  202|422|400|401) pass "POST /api/v1/rag/build → $STATUS (route ok)" ;;
  404)             fail "POST /api/v1/rag/build → 404. Gateway → RAG_BUILDER маршрут не найден" ;;
  502)             fail "POST /api/v1/rag/build → 502. RAG Builder не отвечает" ;;
  000)             fail "Gateway недоступен" ;;
  *)               fail "POST /api/v1/rag/build → $STATUS" ;;
esac

# --------------------------------------------
# 5. RAG Search
# --------------------------------------------
echo ""
echo "── 5. RAG Search ─────────────────────────"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 \
  -X POST "$BASE/api/v1/rag/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"test"}' 2>/dev/null || echo "000")
case "$STATUS" in
  200|422|400|401) pass "POST /api/v1/rag/search → $STATUS (route ok)" ;;
  404)             fail "POST /api/v1/rag/search → 404. Gateway → RAG_SEARCH маршрут не найден" ;;
  502)             fail "POST /api/v1/rag/search → 502. RAG Search не отвечает" ;;
  000)             fail "Gateway недоступен" ;;
  *)               fail "POST /api/v1/rag/search → $STATUS" ;;
esac

# --------------------------------------------
# 6. Orchestrator
# --------------------------------------------
echo ""
echo "── 6. Orchestrator ───────────────────────"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$BASE/api/v1/system/health" 2>/dev/null || echo "000")
case "$STATUS" in
  200|401|403) pass "GET /api/v1/system/health → $STATUS (route ok)" ;;
  404)         fail "GET /api/v1/system/health → 404. Маршрут не найден" ;;
  502)         fail "GET /api/v1/system/health → 502. Orchestrator не отвечает" ;;
  000)         fail "Gateway недоступен" ;;
  *)           fail "GET /api/v1/system/health → $STATUS" ;;
esac

# --------------------------------------------
# 7. Query
# --------------------------------------------
echo ""
echo "── 7. Query ──────────────────────────────"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$BASE/api/v1/query/health" 2>/dev/null || echo "000")
if [ "$STATUS" != "000" ]; then
  pass "GET /api/v1/query/health → $STATUS"
else
  # fallback — query может не иметь отдельного health
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$BASE/api/v1/chat" 2>/dev/null || echo "000")
  case "$STATUS" in
    200|422|400|401) pass "POST /api/v1/chat → $STATUS (route ok)" ;;
    404)             fail "GET /api/v1/chat → 404. Маршрут не найден" ;;
    502)             fail "GET /api/v1/chat → 502. Query не отвечает" ;;
    000)             fail "Gateway недоступен" ;;
    *)               fail "GET /api/v1/chat → $STATUS" ;;
  esac
fi

# --------------------------------------------
# 8. Converter-Validator
# --------------------------------------------
echo ""
echo "── 8. Converter-Validator ────────────────"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$BASE/api/v1/convert" 2>/dev/null || echo "000")
case "$STATUS" in
  200|422|400|401|405) pass "POST /api/v1/convert → $STATUS (route ok)" ;;
  404)                 fail "POST /api/v1/convert → 404. Маршрут не найден" ;;
  502)                 fail "POST /api/v1/convert → 502. Converter не отвечает" ;;
  000)                 fail "Gateway недоступен" ;;
  *)                   fail "POST /api/v1/convert → $STATUS" ;;
esac

# --------------------------------------------
# 9. Parser
# --------------------------------------------
echo ""
echo "── 9. Parser ─────────────────────────────"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 \
  -X POST "$BASE/api/v1/parse" \
  -H "Content-Type: application/json" \
  -d '{"document_id":1}' 2>/dev/null || echo "000")
case "$STATUS" in
  200|422|400|401) pass "POST /api/v1/parse → $STATUS (route ok)" ;;
  404)             fail "POST /api/v1/parse → 404. Маршрут не найден" ;;
  502)             fail "POST /api/v1/parse → 502. Parser не отвечает" ;;
  000)             fail "Gateway недоступен" ;;
  *)               fail "POST /api/v1/parse → $STATUS" ;;
esac

# --------------------------------------------
# Итог
# --------------------------------------------
echo ""
echo "══════════════════════════════════════════════"
echo " Итог: ✅ $PASS passed, ❌ $FAIL failed"
echo "══════════════════════════════════════════════"
echo ""

# Проблема ERR_CONNECTION_REFUSED :8080 — первая проверка
if [ "$PASS" -eq 0 ] && [ "$FAIL" -gt 0 ]; then
  echo "❗ Gateway совсем не отвечает. Возможные причины:"
  echo "   1. Gateway не запущен:  docker compose up -d gateway"
  echo "   2. Gateway слушает не на :8080: проверь GATEWAY_PORT в .env"
  echo "   3. Сервер 195.70.195.203 недоступен: проверь VPN/брандмауэр"
  echo "   4. Старый gateway без обновлений: пересобери docker compose build gateway"
  exit 1
fi
