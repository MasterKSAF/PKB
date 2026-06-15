@echo off
REM =============================================================================
REM PKB Neuroassistant вЂ” re-check: clean DB + restart + full report
REM
REM РђРІС‚РѕРјР°С‚РёС‡РµСЃРєРё:
REM   1. РџСЂРѕРІРµСЂСЏРµС‚ РЅР°Р»РёС‡РёРµ base-РѕР±СЂР°Р·Р° вЂ” РµСЃР»Рё РЅРµС‚, СЃРѕР±РёСЂР°РµС‚
REM   2. РџСЂРѕРІРµСЂСЏРµС‚ РЅР°Р»РёС‡РёРµ РјРѕРґРµР»Рё TEI вЂ” РµСЃР»Рё РЅРµС‚, СЃРєР°С‡РёРІР°РµС‚
REM   3. РџСЂРѕРІРµСЂСЏРµС‚, Р·Р°РїСѓС‰РµРЅ Р»Рё РєРѕРЅС‚РµР№РЅРµСЂ TEI вЂ” РµСЃР»Рё РЅРµС‚, Р·Р°РїСѓСЃРєР°РµС‚
REM   4. Р”СЂРѕРїР°РµС‚ СЃС…РµРјС‹ Р‘Р”, СЃР±СЂР°СЃС‹РІР°РµС‚ Redis, РїРµСЂРµР·Р°РїСѓСЃРєР°РµС‚ app
REM   5. Р—Р°РїСѓСЃРєР°РµС‚ РїРѕР»РЅС‹Р№ РѕС‚С‡С‘С‚ (health + coverage + pipeline)
REM
REM PostgreSQL Рё Redis РЅРµ РїРµСЂРµР·Р°РїСѓСЃРєР°СЋС‚СЃСЏ вЂ” С‚РѕР»СЊРєРѕ С‡РёСЃС‚РёРј РґР°РЅРЅС‹Рµ.
REM TEI РєРѕРЅС‚РµР№РЅРµСЂ РЅРµ РїРµСЂРµР·Р°РїСѓСЃРєР°РµС‚СЃСЏ (С‚СЏР¶С‘Р»Р°СЏ РјРѕРґРµР»СЊ), С‚РѕР»СЊРєРѕ РµСЃР»Рё РЅРµ Р·Р°РїСѓС‰РµРЅ.
REM =============================================================================

cd /d "%~dp0"

echo === PKB Neuroassistant: Re-check ===
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

REM в”Ђв”Ђ 1. РџСЂРѕРІРµСЂРєР° base-РѕР±СЂР°Р·Р° в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
set IMAGE_NAME=ghcr.io/pkb/neuro-base:latest
docker images --format "{{.Repository}}:{{.Tag}}" | findstr /C:"%IMAGE_NAME%" > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [1/5] Base image not found вЂ” building...
    echo.
    set DOCKER_SCOUT_SUPPRESS_ANALYSIS=1
    docker build -f Dockerfile.base -t %IMAGE_NAME% .
    if errorlevel 1 echo WARNING: Build completed with warnings, but image was created.
) else (
    echo [1/5] Base image found, skipping build.
)
echo.

REM в”Ђв”Ђ 2. РџСЂРѕРІРµСЂРєР° РјРѕРґРµР»Рё TEI в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
if not exist "tei_model\model.onnx" (
    echo [2/5] TEI model not found вЂ” downloading...
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

REM в”Ђв”Ђ 3. РџСЂРѕРІРµСЂРєР° РєРѕРЅС‚РµР№РЅРµСЂР° TEI в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
echo [3/5] Checking TEI container status...
docker compose --progress quiet ps --format "{{.State}}" tei 2>nul | findstr /C:"running" > nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo     TEI container is already running, skipping restart.
) else (
    echo     TEI container is NOT running вЂ” starting...
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

REM в”Ђв”Ђ 4. РћС‡РёСЃС‚РєР° РґР°РЅРЅС‹С… + РїРµСЂРµР·Р°РїСѓСЃРє app в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
echo [4/5] Dropping data + restarting app...

echo     Recreating database...
docker exec pkb-postgres psql -U pkb -d postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE datname = 'pkb_neuro' AND pid <> pg_backend_pid();" 2>nul
docker exec pkb-postgres psql -U pkb -d postgres -c "DROP DATABASE IF EXISTS pkb_neuro;" 2>nul
docker exec pkb-postgres psql -U pkb -d postgres -c "CREATE DATABASE pkb_neuro;" 2>nul

echo     Flushing Redis...
docker exec pkb-redis redis-cli FLUSHALL 2>nul

docker compose --progress quiet kill app 2>&1
docker compose --progress quiet rm -f -v app 2>&1
echo.

REM в”Ђв”Ђ 5. Р—Р°РїСѓСЃРє app + РѕС‚С‡С‘С‚ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
echo [5/5] Starting app...
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

echo     Patching RAG Builder tables...
python -m service_checker docker --action patch-rag
if %ERRORLEVEL% neq 0 goto skip_restart

echo     Restarting RAG Builder with proper tables...
docker exec pkb-neuro supervisorctl restart rag-builder 2>nul
:skip_restart

echo.
echo     Running full report...
python -m service_checker docker --action full-report
if %ERRORLEVEL% neq 0 (
    echo.
    echo WARNING: Some checks failed, check the report above.
)

echo.
echo === Done ===
echo Reports: check_result/
echo.
