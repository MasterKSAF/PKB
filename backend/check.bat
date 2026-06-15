@echo off
REM =============================================================================
REM PKB Neuroassistant - quick re-check entry point
REM Calls service_checker/docker/recheck.bat
REM =============================================================================

cd /d "%~dp0"

echo === PKB Neuroassistant: re-check ===
echo.

if not exist "service_checker\docker\.env" (
    if exist "service_checker\docker\.env.example" (
        copy /Y "service_checker\docker\.env.example" "service_checker\docker\.env" >nul
        echo Created service_checker\docker\.env from .env.example
        echo.
    ) else (
        type nul > "service_checker\docker\.env"
        echo Created empty service_checker\docker\.env
        echo.
    )
)

call service_checker\docker\recheck.bat
pause
