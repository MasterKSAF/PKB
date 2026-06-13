@echo off
REM =============================================================================
REM PKB Neuroassistant — re-check: clean DB + restart + full report
REM
REM Автоматически:
REM   1. Проверяет наличие base-образа — если нет, собирает
REM   2. Проверяет наличие модели TEI — если нет, скачивает
REM   3. Проверяет, запущен ли контейнер TEI — если нет, запускает
REM   4. Пересоздаёт контейнеры с чистой БД (kill + rm -v + up)
REM   5. Запускает полный отчёт (health + coverage + pipeline)
REM
REM Каждый запуск начинается с чистой БД — удаляются все volumes.
REM TEI контейнер не перезапускается (тяжёлая модель), только если не запущен.
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

REM ── 3. Проверка контейнера TEI ────────────────────────────────────────────
echo [3/5] Checking TEI container status...
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

REM ── 4. Остановка app + чистка volumes ─────────────────────────────────────
echo [4/5] Killing app + removing volumes...
docker compose --progress quiet kill app postgres redis minio 2>&1
docker compose --progress quiet rm -f -v app postgres redis minio 2>&1
docker volume rm -f pkb_pg_data pkb_minio_data pkb_app_logs 2>nul
echo.

REM ── 5. Запуск контейнеров + полный отчёт ───────────────────────────────────
echo [5/5] Starting containers...
docker compose up -d postgres redis minio app
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start containers!
    pause
    exit /b 1
)
echo     Containers started. Running full report (health + coverage + pipeline)...
echo.

cd /d "%~dp0..\.."
set PYTHONIOENCODING=utf-8
python -m service_checker docker --action full-report
if %ERRORLEVEL% neq 0 (
    echo.
    echo WARNING: Some checks failed, check the report above.
)

echo.
echo === Done ===
echo Reports: check_result/
echo.
