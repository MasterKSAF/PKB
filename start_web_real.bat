@echo off
setlocal enabledelayedexpansion

REM =============================================================================
REM PKB Neuroassistant — Start (Real mode, root docker-compose.yml)
REM
REM Запускает production-стек из корневого docker-compose.yml:
REM   PostgreSQL, Redis, MinIO, Infinity (reranker)
REM   + все backend-сервисы (auth, registry, parser, converter-validator,
REM     rag-builder, rag-search, query, orchestrator, gateway)
REM
REM Frontend НЕ запускается (root compose не содержит frontend-сервис).
REM Для запуска frontend используй отдельно:
REM   docker compose -f backend\service_checker\docker\docker-compose-web.yml up -d frontend
REM   или npm run dev в папке UI-UX/UI Final/frontend
REM =============================================================================

cd /d "%~dp0"

echo === PKB Neuroassistant: Start (Real mode) ===
echo.

REM ── 0. Проверка Docker ─────────────────────────────────────────────────────
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker is not running or not installed!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo [0/3] Docker is running.
echo.

REM ── 1. Сборка и запуск всех сервисов ───────────────────────────────────────
echo [1/3] Building and starting all services (root docker-compose.yml)...
echo.
docker compose up -d --build
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start containers!
    pause
    exit /b 1
)
echo.

REM ── 2. Ожидание healthcheck Gateway ────────────────────────────────────────
echo [2/3] Waiting for Gateway...
set /a attempts=0
:wait_gateway
curl -f http://localhost:8080/api/v1/health >nul 2>&1
if %ERRORLEVEL% neq 0 (
    set /a attempts+=1
    if !attempts! geq 30 (
        echo     WARNING: Gateway healthcheck did not pass within timeout.
        goto show_status
    )
    ping -n 3 127.0.0.1 >nul
    goto wait_gateway
)
echo     Gateway is healthy.
echo.

REM ── 3. Статус сервисов ─────────────────────────────────────────────────────
:show_status
echo [3/3] Service status:
echo.
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo.

echo === Done ===
echo.
echo   Backend API (Gateway): http://localhost:8080
echo   Auth Service:          http://localhost:8082
echo   Orchestrator:          http://localhost:8081
echo   Query:                 http://localhost:8083
echo   Registry:              http://localhost:8084
echo   PostgreSQL:            localhost:15432
echo   Redis:                 localhost:16379
echo   MinIO Console:         http://localhost:19001
echo   Infinity (reranker):   http://localhost:18092
echo.
echo   Diagnostics:           http://localhost:8080/api/v1/system/diagnostics
echo.
echo   To stop:
echo     docker compose down
echo.
echo   To start frontend (separately):
echo     docker compose -f backend\service_checker\docker\docker-compose-web.yml up -d frontend
echo     Web UI: http://localhost:3300
echo.

pause
