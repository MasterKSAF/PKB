"""Check env vars in rag-builder process"""
import subprocess
import sys

check_script = """
ENV_VARS=$(cat /proc/$(pidof -s uvicorn)/environ 2>/dev/null | tr '\\0' '\\n' | grep -iE 'dim|embed')
if [ -z "$ENV_VARS" ]; then
    # Try supervisorctl approach
    PID=$(cat /var/run/supervisor/supervisord.pid 2>/dev/null)
    if [ -n "$PID" ]; then
        ENV_VARS=$(cat /proc/$PID/environ 2>/dev/null | tr '\\0' '\\n' | grep -iE 'dim|embed')
    fi
fi
echo "RAG BUILDER ENV VARS:"
echo "$ENV_VARS"
"""

r = subprocess.run(
    ["docker", "exec", "pkb-neuro", "sh", "-c", check_script],
    capture_output=True, text=True, timeout=15
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:500], file=sys.stderr)
