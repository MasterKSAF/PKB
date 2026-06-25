# Diagnostics в Gateway

- [x] Diagnostics встроен в Gateway, а не отдельный сервер
- [x] `GET /api/v1/system/diagnostics` — сводка (конфиг + health сервисов)
- [x] `GET /api/v1/system/diagnostics/{service}` — диагностика по сервису
- [x] Удалены: diagnostics_server.py, Dockerfile, shell-скрипты
- [x] deploy.sh: убрано управление diagnostics (не нужно)
- [x] deploy_reset.sh: вызывает deploy.sh (down + clean + deploy)
- [x] docker-compose.yml: чисто (нет diagnostics сервиса, нет DIAGNOSTICS_URL)
- [x] config.py: удалён diagnostics_url
- [x] README.md: обновлён
