@echo off
if "%1"=="test" (
  py -3.13 -m pytest
  exit /b %errorlevel%
)
echo Unknown target: %1
exit /b 1
