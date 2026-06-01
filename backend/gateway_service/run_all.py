import subprocess, sys, time, os

SERVICES = [
    ("Auth", 8082, "mocks.auth_service.main:app"),
    ("Orchestrator", 8081, "mocks.orchestrator_service.main:app"),
    ("Query", 8083, "mocks.query_service.main:app"),
    ("Registry", 8084, "mocks.registry_service.main:app"),
]

procs = []
for name, port, app in SERVICES:
    print(f"[+] {name} :{port}")
    p = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", app, "--host", "127.0.0.1", "--port", str(port)],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    procs.append((name, p))

print("Все сервисы запущены. Ctrl+C для остановки.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    for n, p in procs:
        p.terminate()
    print("Остановлены.")