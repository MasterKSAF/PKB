@echo off
REM =============================================================================
REM PKB Neuroassistant — re-check: clean DB + restart + full report
REM
REM Автоматически:
REM   0. Проверяет, запущен ли Docker
REM   1. Создаёт .env (если нет — генерирует из create_env.py)
REM   2. Проверяет наличие base-образа — если нет, собирает
REM   3. Проверяет наличие модели TEI — если нет, скачивает
REM   4. Проверяет, запущен ли контейнер TEI — если нет, запускает
REM   5. Дропает схемы БД, сбрасывает Redis, перезапускает app
REM   6. Запускает отчёт (health + coverage + pipeline)
REM   7. Gateway Integration Tests (pytest)
REM
REM Параметры:
REM   --api service1,service2    Только указанные сервисы (через запятую)
REM   --pipeline name1,name2     Только указанные пайплайны
REM   --skip-coverage            Пропустить API Coverage
REM   --skip-pipelines           Пропустить Pipeline тесты
REM   --skip-gateway-tests       Пропустить Gateway Integration Tests (pytest)
REM
REM Примеры:
REM   recheck.bat                                Полный прогон
REM   recheck.bat --api gateway                  Только Gateway
REM   recheck.bat --api gateway --skip-pipelines Только Gateway, без пайплайнов
REM   recheck.bat --pipeline registry_lifecycle  Только один пайплайн
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
if /i "%1"=="--pipeline" (
    set "CLI_ARGS=%CLI_ARGS% --pipelines %2"
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
if /i "%1"=="--skip-gateway-tests" (
    set "CLI_ARGS=%CLI_ARGS% --skip-gateway-tests"
    shift
    goto parse_args
)
REM Неизвестный параметр — игнорируем
shift
goto parse_args
:end_parse

echo === PKB Neuroassistant: Re-check ===
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

REM ── 5. Очистка данных + перезапуск app ────────────────────────────────
echo [5/7] Dropping data + restarting app...

echo     Recreating database...
docker exec pkb-postgres psql -U pkb -d postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE datname = 'pkb_neuro_check' AND pid <> pg_backend_pid();" 2>nul
docker exec pkb-postgres psql -U pkb -d postgres -c "DROP DATABASE IF EXISTS pkb_neuro_check;" 2>nul
docker exec pkb-postgres psql -U pkb -d postgres -c "CREATE DATABASE pkb_neuro_check;" 2>nul

echo     Flushing Redis...
docker exec pkb-redis redis-cli FLUSHALL 2>nul

docker compose --progress quiet kill app 2>&1
docker compose --progress quiet rm -f -v app 2>&1

echo     Removing Orchestrator SQLite db...
set "ORCHESTRATOR_DB=..\..\..\..\PKB_neuroassistant_develop\backend\orchestrator_service\orchestrator.db"
if exist "%ORCHESTRATOR_DB%" (
    del /f /q "%ORCHESTRATOR_DB%" 2>nul
    echo     Deleted %ORCHESTRATOR_DB%
) else (
    echo     Orchestrator SQLite db not found at %ORCHESTRATOR_DB%, trying inside volume...
    rem Fallback: ищем внутри смонтированного backend
    if exist "..\..\orchestrator_service\orchestrator.db" (
        del /f /q "..\..\orchestrator_service\orchestrator.db" 2>nul
        echo     Deleted via fallback path
    )
)
echo.

REM ── 6. Запуск app + отчёт ─────────────────────────────────────────────
echo [6/7] Starting app...
docker compose up -d app
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start app container!
    pause
    exit /b 1
)
echo     App started. Running full report...
echo.

cd /d "%~dp0..\.."
set PYTHONIOENCODING=utf-8

echo     Waiting for supervisor...
:wait_supervisor
docker exec pkb-neuro supervisorctl status 2>nul | findstr "RUNNING" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    ping -n 2 127.0.0.1 >nul
    goto wait_supervisor
)

REM ── Проверка, что развёрнут обычный режим (rag-builder + rag-search) ──
docker exec pkb-neuro supervisorctl status 2>nul | findstr /C:"rag-builder" | findstr "RUNNING" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo     ⚠ Предупреждение: rag-builder не в RUNNING — возможно, развёрнут SPK?
) else (
    docker exec pkb-neuro supervisorctl status 2>nul | findstr /C:"rag-search" | findstr "RUNNING" >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo     ⚠ Предупреждение: rag-search не в RUNNING — возможно, развёрнут SPK?
    ) else (
        echo     ✅ Обычный режим: rag-builder + rag-search RUNNING
    )
)

echo     RAG Builder tables are now handled by Alembic migrations (no patching needed).

echo.
if defined CLI_ARGS (
    echo     Running: python -m service_checker docker --action full-report%CLI_ARGS%
    echo.
    python -m service_checker docker --action full-report%CLI_ARGS%
) else (
    echo     Running full report...
    echo.
    python -m service_checker docker --action full-report
)
if %ERRORLEVEL% neq 0 (
    echo.
    echo WARNING: Some checks failed, check the report above.
)


REM ── 7. Gateway Integration Tests ─────────────────────────────────────
echo [7/7] Running Gateway Integration Tests...
echo.

REM Запускаем pytest напрямую (не через service_checker)
REM Текущая директория: backend\ (cd /d "%~dp0..\.." выше)
python -m pytest gateway_service\tests\ -v --tb=short --no-header -p no:warnings > "check_result\gateway_tests.md" 2>&1
set GATEWAY_EXIT=%ERRORLEVEL%

REM Выводим краткую статистику
findstr /R ".*passed.*failed.*" "check_result\gateway_tests.md" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo.
    findstr /R ".*passed.*failed.*" "check_result\gateway_tests.md"
)

if %GATEWAY_EXIT% equ 0 (
    echo     Gateway tests: ALL PASSED ^(see check_result\gateway_tests.md^)
) else (
    echo     Gateway tests: SOME FAILED ^(exit=%GATEWAY_EXIT%^) ^(see check_result\gateway_tests.md^)
)
echo.

echo === Done ===
echo Reports: check_result/
echo.
