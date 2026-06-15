@echo off
if "%1"=="test" (
  py -3.13 -m pytest
  exit /b %errorlevel%
)
if "%1"=="migrate" (
  py -3.13 -m alembic upgrade head
  exit /b %errorlevel%
)
if "%1"=="downgrade" (
  py -3.13 -m alembic downgrade base
  exit /b %errorlevel%
)
echo Unknown target: %1
exit /b 1
