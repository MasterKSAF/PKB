#!/usr/bin/env python3
"""
PKB Neuroassistant — Diagnostics HTTP Server

Запускает server_diagnostics.sh по HTTP-запросу.
Позволяет получать полную диагностику сервера удалённо (браузер/curl).

Usage:
  python diagnostics_server.py [port]

По умолчанию слушает на 0.0.0.0:9090.
Для остановки: Ctrl+C или kill PID.
"""

import http.server
import subprocess
import sys
import os

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9090

# Переходим в директорию скрипта (чтобы найти server_diagnostics.sh)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

DIAGNOSTICS_SCRIPT = "./server_diagnostics.sh"


class DiagnosticsHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/diagnostics"):
            try:
                result = subprocess.run(
                    [DIAGNOSTICS_SCRIPT],
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
        else:
            body = "404 Not Found\n"
            status = 404

        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format, *args):
        # Тихий лог — только в stdout
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), format % args))


if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), DiagnosticsHandler)
    print(f"Diagnostics server listening on http://0.0.0.0:{PORT}")
    print(f"  → curl http://localhost:{PORT}/diagnostics")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
