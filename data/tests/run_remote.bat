@echo off
REM Run all server tests against remote server
REM Usage: data\tests\run_remote.bat

set TEST_API_URL=http://195.70.195.203:8080/api/v1
cd /d "%~dp0.."

echo ==========================================
echo  Target: %TEST_API_URL%
echo ==========================================
echo.

REM Quick connectivity check
python -c "import requests; r=requests.post('%TEST_API_URL%/auth/token', json={'username':'admin@example.com','password':'Admin1234!'}, timeout=10); assert r.status_code==200; print('  [OK] Server reachable, auth works')" 2>nul
if %ERRORLEVEL% neq 0 (
    python -c "import requests; r=requests.post('%TEST_API_URL%/auth/token', json={'username':'admin@example.com','password':'Admin1234!'}, timeout=10); assert r.status_code==200; print('  [OK] Server reachable, auth works')"
    echo   [FAIL] Cannot reach server
    pause
    exit /b 1
)

echo.
echo --- test_go.py (fast) ---
python data/tests\test_go.py
if %ERRORLEVEL% neq 0 echo   [FAIL] test_go.py exited with code %ERRORLEVEL%

echo.
echo --- test_quick.py (with preview wait) ---
python data/tests\test_quick.py
if %ERRORLEVEL% neq 0 echo   [FAIL] test_quick.py exited with code %ERRORLEVEL%

echo.
echo --- test_e2e.py (full E2E) ---
python data/tests\test_e2e.py
if %ERRORLEVEL% neq 0 echo   [FAIL] test_e2e.py exited with code %ERRORLEVEL%

echo.
echo --- test_full_pipeline.py (extended) ---
python data/tests\test_full_pipeline.py
if %ERRORLEVEL% neq 0 echo   [FAIL] test_full_pipeline.py exited with code %ERRORLEVEL%

echo.
echo ==========================================
echo  DONE
echo ==========================================
pause
