@echo off
REM =============================================================================
REM PKB Neuroassistant — re-check: restart/start containers + health + coverage
REM Run from backend/ (via check.bat) or directly from this directory.
REM =============================================================================

cd /d "%~dp0..\.."

set COMPOSE_FILE=service_checker\docker\docker-compose.yml
set SERVICE_CHECKER=service_checker\service_checker.py

docker inspect pkb-neuro > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [1/3] Container not found — starting...
    docker compose -f %COMPOSE_FILE% up -d
) else (
    echo [1/3] Restarting container...
    docker compose -f %COMPOSE_FILE% restart app
)

echo.
echo [2/3] Waiting 10 seconds...
ping -n 11 127.0.0.1 > nul

echo.
echo [3/3] Running coverage check...
python %SERVICE_CHECKER% docker --action coverage

echo.
echo Done. Reports saved to check_result/
echo.

pause
