@echo off
:: =============================================================================
:: PKB Neuroassistant — Deploy with Reset (clean + deploy) [Windows]
::
:: Полный сброс данных (удаление volumes БД и MinIO) и развёртывание.
:: ВНИМАНИЕ: все данные (БД, объектное хранилище) будут удалены!
::
:: Останавливает сервисы, чистит volumes, затем вызывает deploy.bat.
:: =============================================================================

setlocal enabledelayedexpansion

:: ── ANSI цвета ──────────────────────────────────────────────────────────────
for /f %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "RED=%ESC%[91m"
set "GREEN=%ESC%[92m"
set "YELLOW=%ESC%[93m"
set "NC=%ESC%[0m"

cd /d "%~dp0"

echo %RED%============================================%NC%
echo %RED%  PKB Neuroassistant — Deploy with RESET%NC%
echo %RED%  WARNING: All data will be destroyed!%NC%
echo %RED%============================================%NC%
echo.

:: ── Подтверждение ───────────────────────────────────────────────────────────
:check_input
set /p "REPLY=Are you sure you want to delete ALL data and redeploy? [y/N] "
if not defined REPLY set "REPLY=n"
echo(!REPLY!| findstr /ri "^y$" >nul
if errorlevel 1 (
    echo Cancelled.
    exit /b 0
)
echo.

:: ── 1. Остановка сервисов ────────────────────────────────────────────────────
echo %YELLOW%[1/3] Stopping services...%NC%
docker compose down
echo.

:: ── 2. Удаление volumes (huggingface_cache — кеш Infinity — оставляем) ───────
echo %YELLOW%[2/3] Removing data volumes (pg_data, minio_data)...%NC%

:: Определяем имя проекта из docker-compose.yml (fallback — имя папки)
set "PROJECT_NAME="
for /f "usebackq tokens=2 delims=: " %%a in (`findstr /b "name:" docker-compose.yml 2^>nul`) do (
    set "PROJECT_NAME=%%a"
)
if not defined PROJECT_NAME (
    for %%a in ("%cd%") do set "PROJECT_NAME=%%~nxa"
)

:: Удаляем volumes по точному имени (<project>_<volume>)
docker volume rm %PROJECT_NAME%_pg_data %PROJECT_NAME%_minio_data 2>nul
echo   %GREEN%Data volumes removed.%NC%
echo.

:: ── 3. Вызов deploy.bat ──────────────────────────────────────────────────────
echo %YELLOW%[3/3] Running deploy.bat...%NC%
echo.
call "%~dp0deploy.bat"
