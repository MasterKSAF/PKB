@echo off
REM =============================================================================
REM PKB Neuroassistant — re-check: prepare missing deps + restart + full report
REM
REM Автоматически:
REM   1. Проверяет наличие base-образа — если нет, собирает
REM   2. Проверяет наличие модели TEI — если нет, скачивает
REM   3. Запускает / перезапускает контейнеры
REM   4. Ждёт и запускает full-report
REM
REM БЕЗ очистки volumes (данные сохраняются).
REM Для полной переустановки с нуля: docker\prepare.bat
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

REM ── 3. Запуск / перезапуск контейнеров ────────────────────────────────────
cd /d "%~dp0..\.."
set COMPOSE_FILE=service_checker\docker\docker-compose.yml

docker inspect pkb-neuro > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [3/5] Containers not found — starting all...
    docker compose -f %COMPOSE_FILE% up -d
) else (
    echo [3/5] Restarting app container...
    docker compose -f %COMPOSE_FILE% restart app
)
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start containers!
    pause
    exit /b 1
)
echo.

echo [4/5] Waiting 10 seconds for services to initialize...
ping -n 11 127.0.0.1 > nul
echo.

echo [5/5] Running full report (coverage + pipelines)...
python -m service_checker docker --action full-report
if %ERRORLEVEL% neq 0 (
    echo.
    echo WARNING: Some checks failed, check the report above.
)

echo.
echo === Done ===
echo Reports: check_result/
echo For full reset (wipe volumes): docker\prepare.bat
echo.

pause
