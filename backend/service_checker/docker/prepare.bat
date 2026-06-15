@echo off
REM =============================================================================
REM PKB Neuroassistant вЂ” initial setup from scratch (one time after git clone)
REM
REM РџРѕР»РЅС‹Р№ С†РёРєР»: РїРѕРґРіРѕС‚РѕРІРєР° РјРѕРґРµР»Рё TEI + СЃР±РѕСЂРєР° РѕР±СЂР°Р·Р° + РѕС‡РёСЃС‚РєР° volumes +
REM              Р·Р°РїСѓСЃРє РєРѕРЅС‚РµР№РЅРµСЂРѕРІ + full-report РїСЂРѕРІРµСЂРєР°.
REM
REM РСЃРїРѕР»СЊР·СѓР№С‚Рµ РєРѕРіРґР° РЅСѓР¶РЅРѕ РїРѕРґРЅСЏС‚СЊ РІСЃС‘ СЃ РЅСѓР»СЏ:
REM   docker\prepare.bat
REM
REM Р”Р»СЏ РїРѕРІС‚РѕСЂРЅРѕРіРѕ Р·Р°РїСѓСЃРєР° (Р±РµР· СЃР±СЂРѕСЃР° volumes) РёСЃРїРѕР»СЊР·СѓР№С‚Рµ:
REM   docker\recheck.bat
REM =============================================================================

cd /d "%~dp0"

echo === PKB Neuroassistant: Full setup from scratch ===
echo.

if not exist ".env" (
    if exist ".env.example" (
        copy /Y ".env.example" ".env" >nul
        echo Created .env from .env.example
        echo.
    ) else (
        type nul > ".env"
        echo Created empty .env
        echo.
    )
)

echo [1/7] Preparing TEI model (if not already cached)...
echo.
python prepare_tei_model.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: TEI model preparation failed!
    pause
    exit /b 1
)
echo.

echo [2/7] Building base image (Python + dependencies)...
echo.
set DOCKER_SCOUT_SUPPRESS_ANALYSIS=1
docker build -f Dockerfile.base -t ghcr.io/pkb/neuro-base:latest .
if errorlevel 1 (
    echo.
    echo WARNING: Build completed with warnings, but image was created.
)
echo.

REM РЎРЅР°С‡Р°Р»Р° РјРёРіСЂРёСЂСѓРµРј СЃС‚Р°СЂС‹Рµ volumes (docker_* -> pkb_*), РµСЃР»Рё РѕРЅРё РµСЃС‚СЊ
echo [3/7] Migrating old volumes (docker_* -> pkb_*)...
python migrate_volumes.py
echo.

echo [4/7] Stopping containers...
docker compose -f docker-compose.yml down
echo.

echo [4/7] Removing known data volumes (DB, MinIO, logs)...
docker volume rm -f pkb_pg_data pkb_minio_data pkb_app_logs 2>nul
echo.

echo [5/7] Starting all containers (PostgreSQL, Redis, MinIO, TEI, App)...
docker compose -f docker-compose.yml up -d
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start containers!
    pause
    exit /b 1
)
echo.

echo [6/7] Waiting 10 seconds for services to initialize...
ping -n 11 127.0.0.1 > nul
echo.

echo [7/7] Running full report (coverage + pipelines)...
for %%I in ("%~dp0..\..") do cd /d "%%~fI"
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
