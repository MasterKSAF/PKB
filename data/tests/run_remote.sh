#!/usr/bin/env sh
# Run all server tests against remote server
# Usage: sh data/tests/run_remote.sh
# Or:   ./data/tests/run_remote.sh  (if +x)

export TEST_API_URL=http://195.70.195.203:8080/api/v1
cd "$(dirname "$0")/.."   # project root

echo "=========================================="
echo " Target: $TEST_API_URL"
echo "=========================================="
echo ""

# Quick connectivity check
python -c "
import requests
try:
    r = requests.post('${TEST_API_URL}/auth/token',
        json={'username':'admin@example.com','password':'Admin1234!'}, timeout=10)
    assert r.status_code == 200
    print('  [OK] Server reachable, auth works')
except Exception as e:
    print(f'  [FAIL] Cannot reach server: {e}')
    exit(1)
" || exit 1

echo ""
echo "--- test_go.py (fast) ---"
python data/tests/test_go.py || echo "  [FAIL] test_go.py exited with code $?"

echo ""
echo "--- test_quick.py (with preview wait) ---"
python data/tests/test_quick.py || echo "  [FAIL] test_quick.py exited with code $?"

echo ""
echo "--- test_e2e.py (full E2E) ---"
python data/tests/test_e2e.py || echo "  [FAIL] test_e2e.py exited with code $?"

echo ""
echo "--- test_full_pipeline.py (extended) ---"
python data/tests/test_full_pipeline.py || echo "  [FAIL] test_full_pipeline.py exited with code $?"

echo ""
echo "=========================================="
echo " DONE"
echo "=========================================="
