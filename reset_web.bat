@echo off
REM =============================================================================
REM PKB Neuroassistant — Reset Backend + Web UI
REM
REM Сброс данных и перезапуск (без пересборки образов):
REM   0. Проверяет, запущен ли Docker
REM   1. Создаёт .env (если нет — генерирует из create_env.py)
REM   2. Проверяет наличие base-образа — если нет, собирает
REM   3. Проверяет наличие модели TEI — если нет, скачивает
REM   4. Проверяет, запущен ли контейнер TEI — если нет, запускает
REM   5. Дропает БД, сбрасывает Redis, перезапускает app + frontend
REM   6. Ожидает supervisor
REM   7. Показывает статус сервисов
REM =============================================================================

cd /d "%~dp0\backend\service_checker\docker"

echo === PKB Neuroassistant: Reset Backend + Web UI ===
echo.

REM ── 0. Проверка Docker ─────────────────────────────────────────────────────
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Docker is not running or not installed!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo [0/7] Docker is running.
echo.

REM ── 1. Создание .env ───────────────────────────────────────────────────────
echo [1/7] Generating .env...
python create_env.py
echo.

REM ── 2. Проверка base-образа ────────────────────────────────────────────────
set IMAGE_NAME=ghcr.io/pkb/neuro-base:latest
docker images --format "{{.Repository}}:{{.Tag}}" | findstr /C:"%IMAGE_NAME%" > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [2/7] Base image not found — building...
    echo.
    set DOCKER_SCOUT_SUPPRESS_ANALYSIS=1
    copy "..\..\..\UI-UX\UI Final\frontend\package*.json" . >nul 2>&1
    docker build -f Dockerfile.base -t %IMAGE_NAME% .
    if errorlevel 1 echo WARNING: Build completed with warnings, but image was created.
) else (
    echo [2/7] Base image found, skipping build.
)
echo.

REM ── 3. Проверка модели TEI ─────────────────────────────────────────────────
if not exist "tei_model\model.onnx" (
    echo [3/7] TEI model not found — downloading...
    echo.
    python prepare_tei_model.py
    if %ERRORLEVEL% neq 0 (
        echo.
        echo ERROR: TEI model preparation failed!
        pause
        exit /b 1
    )
) else (
    echo [3/7] TEI model found, skipping download.
)
echo.

REM ── 4. Проверка контейнера TEI ────────────────────────────────────────────
echo [4/7] Checking TEI container status...
docker compose --progress quiet ps --format "{{.State}}" tei 2>nul | findstr /C:"running" > nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo     TEI container is already running, skipping restart.
) else (
    echo     TEI container is NOT running — starting...
    docker compose --progress quiet up -d tei
    timeout /t 3 /nobreak >nul
    docker compose --progress quiet ps --format "{{.State}}" tei 2>nul | findstr /C:"running" > nul 2>&1
    if %ERRORLEVEL% equ 0 (
        echo     TEI container started.
    ) else (
        echo     WARNING: Failed to start TEI container, continuing anyway.
    )
)
echo.

REM ── 5. Сброс данных + перезапуск сервисов ─────────────────────────────
echo [5/7] Dropping data + restarting services...
echo.

echo     Recreating database...
docker exec pkb-postgres psql -U pkb -d postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE datname = 'pkb_neuro' AND pid <> pg_backend_pid();" 2>nul
docker exec pkb-postgres psql -U pkb -d postgres -c "DROP DATABASE IF EXISTS pkb_neuro;" 2>nul
docker exec pkb-postgres psql -U pkb -d postgres -c "CREATE DATABASE pkb_neuro;" 2>nul

echo     Flushing Redis...
docker exec pkb-redis redis-cli FLUSHALL 2>nul

docker compose -f docker-compose-web.yml --progress quiet kill app frontend 2>&1
docker compose -f docker-compose-web.yml --progress quiet rm -f -v app frontend 2>&1
echo.

REM ── 6. Запуск app + frontend ──────────────────────────────────────────────
echo [6/7] Starting app + frontend...
docker compose -f docker-compose-web.yml up -d app frontend
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start containers!
    pause
    exit /b 1
)
echo     Services started.
echo.

REM ── 7. Ожидание supervisor ─────────────────────────────────────────────────
echo [7/7] Waiting for supervisor...
:wait_supervisor
docker exec pkb-neuro supervisorctl status 2>nul | findstr "RUNNING" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    ping -n 2 127.0.0.1 >nul
    goto wait_supervisor
)

REM ── Статус сервисов ────────────────────────────────────────────────────────
echo.
echo === Backend Services (supervisord) ===
docker exec pkb-neuro supervisorctl status 2>nul
echo.
echo === Docker containers ===
docker compose -f docker-compose-web.yml ps
echo.

echo === Done ===
echo.
echo   Backend API:       http://localhost:8080
echo   Web UI:            http://localhost:3300
echo.

start http://localhost:3300
start http://localhost:8080/api/v1/health

pause
