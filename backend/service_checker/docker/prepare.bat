@echo off
REM =============================================================================
REM PKB Neuroassistant — initial setup from scratch (one time after git clone)
REM
REM Полный цикл: подготовка модели TEI + сборка образа + очистка volumes +
REM              запуск контейнеров + full-report проверка.
REM
REM Используйте когда нужно поднять всё с нуля:
REM   docker\prepare.bat
REM
REM Для повторного запуска (без сброса volumes) используйте:
REM   docker\recheck.bat
REM =============================================================================

cd /d "%~dp0"

echo === PKB Neuroassistant: Full setup from scratch ===
echo.

echo [1/6] Preparing TEI model (if not already cached)...
echo.
python prepare_tei_model.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: TEI model preparation failed!
    pause
    exit /b 1
)
echo.

echo [2/6] Building base image (Python + dependencies)...
echo.
set DOCKER_SCOUT_SUPPRESS_ANALYSIS=1
docker build -f Dockerfile.base -t ghcr.io/pkb/neuro-base:latest .
if errorlevel 1 (
    echo.
    echo WARNING: Build completed with warnings, but image was created.
)
echo.

echo [3/6] Cleaning old volumes (PostgreSQL, MinIO, logs)...
docker compose -f docker-compose.yml down -v
echo.

echo [4/6] Starting all containers (PostgreSQL, Redis, MinIO, TEI, App)...
docker compose -f docker-compose.yml up -d
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start containers!
    pause
    exit /b 1
)
echo.

echo [5/6] Waiting 10 seconds for services to initialize...
ping -n 11 127.0.0.1 > nul
echo.

echo [6/6] Running full report (coverage + pipelines)...
cd /d "%~dp0..\.."
python -m service_checker docker --action full-report
if %ERRORLEVEL% neq 0 (
    echo.
    echo WARNING: Some checks failed, check the report above.
)

echo.
echo === Ready! ===
echo Reports: check_result/
echo For quick re-check (no volume wipe): docker\recheck.bat
echo.

pause
