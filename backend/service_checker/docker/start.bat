@echo off
REM =============================================================================
REM PKB Neuroassistant — start: просто запуск сервера
REM
REM Автоматически:
REM   0. Проверяет, запущен ли Docker
REM   1. Создаёт .env (если нет — генерирует из create_env.py)
REM   2. Проверяет наличие base-образа — если нет, собирает
REM   3. Проверяет наличие модели TEI — если нет, скачивает
REM   4. Проверяет, запущен ли контейнер TEI — если нет, запускает
REM   5. Запускает app (без сброса БД/Redis)
REM   6. Ожидает supervisor
REM   7. Показывает статус сервисов
REM
REM Отличие от recheck.bat:
REM   — Не дропает БД, не сбрасывает Redis, не пересоздаёт контейнер app
REM   — Не запускает full-report (только запуск и проверка статуса)
REM =============================================================================

cd /d "%~dp0"

echo === PKB Neuroassistant: Start Server ===
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

REM ── 4. Проверка контейнера TEI ────────────────────────────────────────────
echo [4/6] Checking TEI container status...
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

REM ── 5. Запуск app (без сброса данных) ──────────────────────────────────
echo [5/6] Starting app (preserving data)...
docker compose up -d app
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start app container!
    pause
    exit /b 1
)
echo     App started.
echo.

cd /d "%~dp0..\.."
set PYTHONIOENCODING=utf-8

echo [6/6] Waiting for supervisor...
:wait_supervisor
docker exec pkb-neuro supervisorctl status 2>nul | findstr "RUNNING" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    ping -n 2 127.0.0.1 >nul
    goto wait_supervisor
)

REM ── Показываем статус всех сервисов ────────────────────────────────────────
echo.
echo === Service Status ===
docker exec pkb-neuro supervisorctl status 2>nul
echo.

echo === Done ===
echo Server is running. Use docker compose ps to see all containers.
echo.
