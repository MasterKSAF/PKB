@echo off
REM =============================================================================
REM PKB Neuroassistant — re-check SPD: RAG Builder SPD
REM
REM Использует docker-compose.spd.yml (rag-builder-spk вместо rag-builder + rag-search).
REM Отчёты с суффиксом _spd.
REM =============================================================================
REM Параметры:
REM   --api service1,service2    Только указанные сервисы
REM   --skip-coverage            Пропустить API Coverage
REM =============================================================================

cd /d "%~dp0"

REM ── Парсинг параметров ─────────────────────────────────────────────────────
set "CLI_ARGS="

:parse_args
if "%1"=="" goto end_parse
if /i "%1"=="--api" (
    set "CLI_ARGS=%CLI_ARGS% --services %2"
    shift
    shift
    goto parse_args
)
if /i "%1"=="--skip-coverage" (
    set "CLI_ARGS=%CLI_ARGS% --skip-coverage"
    shift
    goto parse_args
)
if /i "%1"=="--skip-pipelines" (
    set "CLI_ARGS=%CLI_ARGS% --skip-pipelines"
    shift
    goto parse_args
)
shift
goto parse_args
:end_parse

set "COMPOSE=docker compose -f docker-compose.yml -f docker-compose.spd.yml"

echo === PKB Neuroassistant: Re-check SPD (RAG Builder SPD) ===
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
%COMPOSE% --progress quiet ps --format "{{.State}}" tei 2>nul | findstr /C:"running" > nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo     TEI container is already running, skipping restart.
) else (
    echo     TEI container is NOT running — starting...
    %COMPOSE% --progress quiet up -d tei
    timeout /t 3 /nobreak >nul
    %COMPOSE% --progress quiet ps --format "{{.State}}" tei 2>nul | findstr /C:"running" > nul 2>&1
    if %ERRORLEVEL% equ 0 (
        echo     TEI container started.
    ) else (
        echo     WARNING: Failed to start TEI container, continuing anyway.
    )
)
echo.

REM ── 5. Очистка данных + перезапуск app ────────────────────────────────
echo [5/7] Dropping data + restarting app...

echo     Recreating database...
docker exec pkb-postgres psql -U pkb -d postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE datname = 'pkb_neuro' AND pid <> pg_backend_pid();" 2>nul
docker exec pkb-postgres psql -U pkb -d postgres -c "DROP DATABASE IF EXISTS pkb_neuro;" 2>nul
docker exec pkb-postgres psql -U pkb -d postgres -c "CREATE DATABASE pkb_neuro;" 2>nul

echo     Flushing Redis...
docker exec pkb-redis redis-cli FLUSHALL 2>nul

%COMPOSE% --progress quiet kill app 2>&1
%COMPOSE% --progress quiet rm -f -v app 2>&1
echo.

REM ── 6. Запуск app + отчёт ─────────────────────────────────────────────
echo [6/7] Starting app...
%COMPOSE% up -d app
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start app container!
    pause
    exit /b 1
)
echo     App started. Running SPD report...
echo.

cd /d "%~dp0..\.."
set PYTHONIOENCODING=utf-8

set "SPD_CTR=pkb-neuro"

echo     Waiting for supervisor...
:wait_supervisor
docker exec %SPD_CTR% supervisorctl status 2>nul | findstr "RUNNING" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    ping -n 2 127.0.0.1 >nul
    goto wait_supervisor
)

REM ── Проверка, что развёрнут SPD-режим (rag-builder-spk RUNNING, без rag-search) ──
docker exec %SPD_CTR% supervisorctl status 2>nul | findstr /C:"rag-builder-spk" | findstr "RUNNING" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo     ⚠ Предупреждение: rag-builder-spk не в RUNNING — возможно, развёрнут обычный режим?
) else (
    docker exec %SPD_CTR% supervisorctl status 2>nul | findstr /C:"rag-search" >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        echo     ⚠ Предупреждение: rag-search найден — возможно, развёрнут обычный режим?
    ) else (
        echo     ✅ SPD-режим: rag-builder-spk RUNNING (без rag-search)
    )
)

echo.
echo     Running: python -m service_checker docker --action full-report --spd%CLI_ARGS%
echo.
python -m service_checker docker --action full-report --spd%CLI_ARGS%
if %ERRORLEVEL% neq 0 (
    echo.
    echo WARNING: Some checks failed, check the report above.
)

echo.
echo === Done ===
echo Reports: check_result/api_coverage_spd.md, check_result/full_report_spd.md
echo.
