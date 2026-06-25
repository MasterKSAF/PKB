# Diagnostics: компактная сводка + надёжный запуск

- [x] Базовая диагностика → компактная (system + health + containers ✓/✗ + git)
- [x] `?verbose=true` → полная (диски, Docker, порты, логи ошибок, system)
- [x] `/diagnostics/{service}` → диагностика конкретного сервиса
- [x] `/health` → health-check эндпоинт для diagnostics_server.py
- [x] `--pidfile` аргумент для diagnostics_server.py
- [x] Graceful shutdown через SIGTERM/SIGINT
- [x] Удалены server_diagnostics.sh и start_diagnostics_server.sh
- [x] deploy.sh/deploy_reset.sh: PID-файл, проверка через /health, без дублей
- [x] Все ссылки на shell → python3 diagnostics_server.py 9090
