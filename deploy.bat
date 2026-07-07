@echo off
:: =============================================================================
:: PKB Neuroassistant — Deploy (git pull + docker compose up) [Windows]
::
:: Обновление из git и развёртывание всех сервисов (корневой docker-compose.yml).
:: Сохраняет существующие volumes (база данных, MinIO).
:: =============================================================================

setlocal enabledelayedexpansion

:: ── ANSI цвета ──────────────────────────────────────────────────────────────
for /f %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "RED=%ESC%[91m"
set "GREEN=%ESC%[92m"
set "YELLOW=%ESC%[93m"
set "CYAN=%ESC%[96m"
set "NC=%ESC%[0m"

cd /d "%~dp0"

echo %CYAN%============================================%NC%
echo %CYAN%  PKB Neuroassistant — Deploy%NC%
echo %CYAN%============================================%NC%
echo.

:: ── 0. Проверка Docker ───────────────────────────────────────────────────────
echo %YELLOW%[0/4] Checking Docker...%NC%
docker info >nul 2>&1
if errorlevel 1 (
    echo %RED%ERROR: Docker is not running!%NC%
    pause
    exit /b 1
)
echo   %GREEN%Docker is running.%NC%
echo.

:: ── 1. Git pull ──────────────────────────────────────────────────────────────
::echo %YELLOW%[1/4] Pulling latest code from git...%NC%
::git pull 2>&1
::if errorlevel 1 (
    ::  echo   %YELLOW%Pull failed, force checkout...%NC%
    :: git fetch origin
    :: git checkout origin/develop -- . 2>nul
::)
:: git fetch --unshallow 2>nul || ver>nul
:: echo   %GREEN%Git updated.%NC%
::echo.

:: ── 2. Сборка и запуск ──────────────────────────────────────────────────────
echo %YELLOW%[2/4] Building and starting all services...%NC%

:: Получаем GIT_COMMIT
for /f %%g in ('git rev-parse HEAD 2^>nul') do set "GIT_COMMIT=%%g"
if not defined GIT_COMMIT set "GIT_COMMIT=unknown"

:: BUILD_TIME в UTC
for /f %%t in ('wmic os get localdatetime 2^>nul ^| findstr 2') do set "DT=%%t"
if defined DT (
    set "BUILD_TIME=!DT:~0,4!-!DT:~4,2!-!DT:~6,2!T!DT:~8,2!:!DT:~10,2!:!DT:~12,2!Z"
) else (
    set "BUILD_TIME=unknown"
)

set "GIT_COMMIT=%GIT_COMMIT%"
set "BUILD_TIME=%BUILD_TIME%"

docker compose up -d --build
echo   %GREEN%All containers started.%NC%
echo.

:: ── 3. Метка времени деплоя ──────────────────────────────────────────────────
:: Сохраняем timestamp в UTC
for /f %%t in ('wmic os get localdatetime 2^>nul ^| findstr 2') do set "DT=%%t"
if defined DT (
    set "TIMESTAMP=!DT:~0,4!-!DT:~4,2!-!DT:~6,2!T!DT:~8,2!:!DT:~10,2!:!DT:~12,2!Z"
    echo !TIMESTAMP!> .deployed
)
echo   %GREEN%Deploy timestamp saved.%NC%
echo.

:: ── 4. Ожидание инициализации ───────────────────────────────────────────────
echo %YELLOW%[3/4] Waiting for services to initialize (10s)...%NC%
timeout /t 10 /nobreak >nul
echo.

:: ── 5. Статус и health ──────────────────────────────────────────────────────
echo %YELLOW%[4/4] Service status:%NC%
docker compose ps

echo.
echo %YELLOW%[4/4] Health check (Gateway):%NC%

:: Проверка curl (доступен в Windows 10 1903+ / Git Bash / Docker Desktop)
where curl >nul 2>&1
if errorlevel 1 (
    echo   %YELLOW%curl not found, skipping health check.%NC%
) else (
    for /f %%c in ('curl -s -o nul -w "%%{http_code}" --connect-timeout 5 http://localhost:8080/health 2^>nul') do set "HEALTH=%%c"
    if not defined HEALTH set "HEALTH=000"
    if "!HEALTH!"=="200" (
        echo   Gateway health: %GREEN%!HEALTH! OK%NC%
    ) else (
        echo   Gateway health: %RED%!HEALTH!%NC% (expected 200)
    )
)

echo.
echo %GREEN%=== Deploy complete ===%NC%
echo.
echo   Backend API:     http://localhost:8080
echo   Web UI:          http://localhost:3300
echo   Diagnostics:     http://localhost:8080/api/v1/system/diagnostics
echo.
echo   To view logs:    docker compose logs -f
echo   To stop:         docker compose down
echo.
pause
