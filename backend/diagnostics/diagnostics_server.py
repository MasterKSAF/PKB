#!/usr/bin/env python3
"""
PKB Neuroassistant — Diagnostics HTTP Server

Запускает server_diagnostics.sh с аргументами в зависимости от пути запроса.

Роутинг:
  GET /diagnostics              → базовая сводка (--summary)
  GET /diagnostics/{service}    → диагностика одного сервиса (--service {service})
  GET /diagnostics/system       → системные логи (--verbose без summary)
  GET /diagnostics?verbose=true → расширенная сводка
  GET /diagnostics?logs=100     → с указанием количества строк логов

Usage:
  python diagnostics_server.py [port]

По умолчанию слушает на 0.0.0.0:9090.
"""

import http.server
import subprocess
import sys
import os
from urllib.parse import urlparse, parse_qs

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9090

# Переходим в директорию скрипта (чтобы найти server_diagnostics.sh)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

DIAGNOSTICS_SCRIPT = "./server_diagnostics.sh"

# Известные сервисы (для валидации)
KNOWN_SERVICES = {
    "gateway", "orchestrator", "parser", "converter-validator",
    "rag-builder", "rag-search", "registry", "auth", "query",
    "postgres", "redis", "minio", "infinity",
}


class DiagnosticsHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        # Параметры
        verbose = params.get("verbose", [None])[0] in ("true", "1", "yes")
        logs_n = params.get("logs", [None])[0]
        logs_arg = int(logs_n) if logs_n and logs_n.isdigit() else 20

        # Определяем команду в зависимости от пути
        if path in ("", "/diagnostics"):
            # Базовая сводка
            cmd = [DIAGNOSTICS_SCRIPT, "--summary"]
            if verbose:
                cmd.append("--verbose")
            if logs_n:
                cmd += ["--logs", str(logs_arg)]

        elif path.startswith("/diagnostics/"):
            service = path.split("/")[-1]

            if service == "system":
                # Только системные логи
                cmd = [DIAGNOSTICS_SCRIPT, "--verbose", "--logs", "100"]

            elif service in KNOWN_SERVICES:
                # Диагностика конкретного сервиса
                cmd = [DIAGNOSTICS_SCRIPT, "--service", service]
                if verbose:
                    cmd.append("--verbose")
                if logs_n:
                    cmd += ["--logs", str(logs_arg)]
            else:
                body = f"Unknown service: {service}\n"
                body += f"Known services: {', '.join(sorted(KNOWN_SERVICES))}\n"
                self._respond(404, body)
                return
        else:
            body = "404 Not Found\n"
            self._respond(404, body)
            return

        # Запускаем скрипт
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            body = result.stdout
            if result.stderr:
                body += "\n--- stderr ---\n" + result.stderr
            status = 200
        except subprocess.TimeoutExpired:
            body = "ERROR: diagnostics script timed out (120s)\n"
            status = 500
        except FileNotFoundError:
            body = f"ERROR: {DIAGNOSTICS_SCRIPT} not found\n"
            status = 500

        self._respond(status, body)

    def _respond(self, status: int, body: str):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format, *args):
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), format % args))


if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), DiagnosticsHandler)
    print(f"Diagnostics server listening on http://0.0.0.0:{PORT}")
    print(f"  → curl http://localhost:{PORT}/diagnostics")
    print(f"  → curl http://localhost:{PORT}/diagnostics/gateway")
    print(f"  → curl http://localhost:{PORT}/diagnostics/system")
    print(f"  → curl http://localhost:{PORT}/diagnostics?verbose=true&logs=50")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
