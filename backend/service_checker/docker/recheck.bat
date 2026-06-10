@echo off
REM =============================================================================
REM PKB Neuroassistant — re-check: clean DB + restart + full report
REM
REM Автоматически:
REM   1. Проверяет наличие base-образа — если нет, собирает
REM   2. Проверяет наличие модели TEI — если нет, скачивает
REM   3. Пересоздаёт контейнеры с чистой БД (down -v + up)
REM   4. Ждёт и запускает full-report
REM
REM Каждый запуск начинается с чистой БД — удаляются все volumes.
REM =============================================================================

cd /d "%~dp0"

echo === PKB Neuroassistant: Re-check ===
echo.

REM ── 1. Проверка base-образа ────────────────────────────────────────────────
set IMAGE_NAME=ghcr.io/pkb/neuro-base:latest
docker images --format "{{.Repository}}:{{.Tag}}" | findstr /C:"%IMAGE_NAME%" > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [1/5] Base image not found — building...
    echo.
    set DOCKER_SCOUT_SUPPRESS_ANALYSIS=1
    docker build -f Dockerfile.base -t %IMAGE_NAME% .
    if errorlevel 1 echo WARNING: Build completed with warnings, but image was created.
) else (
    echo [1/5] Base image found, skipping build.
)
echo.

REM ── 2. Проверка модели TEI ─────────────────────────────────────────────────
if not exist "tei_model\model.onnx" (
    echo [2/5] TEI model not found — downloading...
    echo.
    python prepare_tei_model.py
    if %ERRORLEVEL% neq 0 (
        echo.
        echo ERROR: TEI model preparation failed!
        pause
        exit /b 1
    )
) else (
    echo [2/5] TEI model found, skipping download.
)
echo.

REM ── 3. Пересоздание контейнеров с чистой БД ──────────────────────────────
cd /d "%~dp0..\.."
set COMPOSE_FILE=service_checker\docker\docker-compose.yml

echo [3/5] Stopping containers and removing volumes (clean DB)...
docker compose -f %COMPOSE_FILE% down -v
if %ERRORLEVEL% neq 0 (
    echo.
    echo WARNING: down -v failed, continuing...
)

echo [3/5] Starting containers with fresh database...
docker compose -f %COMPOSE_FILE% up -d
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start containers!
    pause
    exit /b 1
)
echo     Containers are starting with clean database.
echo.

echo [4/5] Waiting 5 seconds for database initialization and service startup...
ping -n 6 127.0.0.1 > nul
echo.

echo [5/5] Running full report (coverage + pipelines + db-check)...
python -m service_checker docker --action full-report
if %ERRORLEVEL% neq 0 (
    echo.
    echo WARNING: Some checks failed, check the report above.
)

echo.
echo === Done ===
echo Reports: check_result/
echo.
