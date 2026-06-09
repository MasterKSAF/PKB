@echo off
REM =============================================================================
REM PKB Neuroassistant — initial setup (one time after git clone)
REM Builds base image, cleans volumes, starts all containers, runs coverage.
REM =============================================================================

cd /d "%~dp0"

echo === PKB Neuroassistant: Initial setup ===
echo.

echo [1/5] Building base image (Python + dependencies)...
echo.
docker build -f Dockerfile.base -t ghcr.io/pkb/neuro-base:latest .
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Base image build failed!
    pause
    exit /b 1
)
echo.

echo [2/5] Cleaning old volumes...
docker compose -f docker-compose.yml down -v
echo.

echo [3/5] Starting all containers (PostgreSQL, Redis, MinIO, Supervisord)...
docker compose -f docker-compose.yml up -d
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start containers!
    pause
    exit /b 1
)
echo.

echo [4/5] Waiting 10 seconds...
ping -n 11 127.0.0.1 > nul
echo.

echo [5/5] Running initial coverage check...
cd /d "%~dp0..\.."
python service_checker\service_checker.py docker --action coverage

echo.
echo === Ready! ===
echo Reports: check_result/
echo For re-check: check.bat
echo.

pause
