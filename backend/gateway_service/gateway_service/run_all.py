import subprocess, sys, os, time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

services = [
    ("Auth", "mocks.auth_service.main:app", 8082),
    ("Query", "mocks.query_service.main:app", 8083),
    ("Registry", "mocks.registry_service.main:app", 8084),
    ("Orchestrator", "mocks.orchestrator_service.main:app", 8085),
]

procs = []
for name, app_path, port in services:
    print(f"[+] Запуск {name} на порту {port}...")
    p = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", app_path, "--host", "127.0.0.1", "--port", str(port)],
        cwd=BASE_DIR
    )
    procs.append(p)
    time.sleep(1)

print("[+] Запуск Gateway на порту 8081...")
gw = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "mocks.gateway.main:app", "--host", "127.0.0.1", "--port", "8081"],
    cwd=BASE_DIR
)
procs.append(gw)

print("\nВсе сервисы запущены. Gateway: http://127.0.0.1:8081/docs")
print("Для остановки нажмите Ctrl+C\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    for p in procs:
        p.terminate()
    print("\n[*] Все сервисы остановлены.")