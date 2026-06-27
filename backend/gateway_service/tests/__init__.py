"""
PKB Neuroassistant — Gateway Service Integration Tests.

Тесты делятся на две категории:
  1. Unit-тесты — импортируют модули gateway напрямую (config, client, rate_limiter, logging_config, diagnostics).
  2. Docker-интеграционные тесты — используют httpx.AsyncClient для вызовов
     к реальному Gateway, запущенному в Docker (http://127.0.0.1:18080).

Для интеграционных тестов требуется работающий Docker с Gateway (recheck.bat).
Если Gateway недоступен — тесты пропускаются (pytest.skip).
"""
