@echo off
REM =============================================================================
REM PKB Neuroassistant - quick re-check entry point
REM Calls service_checker/docker/recheck.bat
REM =============================================================================

cd /d "%~dp0"

call service_checker\docker\recheck_spd.bat
pause
