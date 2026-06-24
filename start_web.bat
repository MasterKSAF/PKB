@echo off
REM =============================================================================
REM PKB Neuroassistant — Start Backend + Web UI
REM
REM Автоматически:
REM   0. Проверяет, запущен ли Docker
REM   1. Создаёт .env (если нет — генерирует из create_env.py)
REM   2. Проверяет наличие base-образа — если нет, собирает
REM   3. Проверяет наличие модели TEI — если нет, скачивает
REM   4. Собирает и запускает все сервисы + frontend (docker-compose-web.yml)
REM   5. Ожидает supervisor
REM   6. Показывает статус сервисов
REM =============================================================================

cd /d "%~dp0\backend\service_checker\docker"

echo === PKB Neuroassistant: Start Backend + Web UI ===
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
echo [0/6] Docker is running.
echo.

REM ── 1. Создание .env ───────────────────────────────────────────────────────
echo [1/6] Generating .env...
python create_env.py
echo.

REM ── 2. Проверка base-образа ────────────────────────────────────────────────
set IMAGE_NAME=ghcr.io/pkb/neuro-base:latest
docker images --format "{{.Repository}}:{{.Tag}}" | findstr /C:"%IMAGE_NAME%" > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [2/6] Base image not found — building...
    echo.
    set DOCKER_SCOUT_SUPPRESS_ANALYSIS=1
    copy "..\..\..\UI-UX\UI Final\frontend\package*.json" . >nul 2>&1
    docker build -f Dockerfile.base -t %IMAGE_NAME% .
    if errorlevel 1 echo WARNING: Build completed with warnings, but image was created.
) else (
    echo [2/6] Base image found, skipping build.
)
echo.

REM ── 3. Проверка модели TEI ─────────────────────────────────────────────────
if not exist "tei_model\model.onnx" (
    echo [3/6] TEI model not found — downloading...
    echo.
    python prepare_tei_model.py
    if %ERRORLEVEL% neq 0 (
        echo.
        echo ERROR: TEI model preparation failed!
        pause
        exit /b 1
    )
) else (
    echo [3/6] TEI model found, skipping download.
)
echo.

REM ── 4. Запуск всех сервисов + frontend ─────────────────────────────────
echo [4/6] Starting all services (infra + backend + frontend)...
echo.

docker compose -f docker-compose-web.yml up -d --build --force-recreate
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start containers!
    pause
    exit /b 1
)
echo     All containers started.
echo.

REM ── 5. Ожидание supervisor ─────────────────────────────────────────────────
echo [5/6] Waiting for supervisor...
:wait_supervisor
docker exec pkb-neuro supervisorctl status 2>nul | findstr "RUNNING" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    ping -n 2 127.0.0.1 >nul
    goto wait_supervisor
)

REM ── 6. Статус сервисов ─────────────────────────────────────────────────────
echo.
echo [6/6] Service status:
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
echo   To stop:
echo     docker compose -f backend\service_checker\docker\docker-compose-web.yml down
echo.

start http://localhost:3300
start http://localhost:8080/api/v1/health

pause
