"""
PKB Neuroassistant Gateway Service.

Reverse-proxy, который маршрутизирует запросы от Web UI к внутренним микросервисам:
  Auth (:8082), Orchestrator (:8081), Query (:8083), Registry (:8084).

Режим работы только явный — GATEWAY_MODE=real (единственный режим).

Мок-сервер для тестирования Web UI — отдельное приложение:
    python mocks/gateway.py
"""

__version__ = "1.1.0"
