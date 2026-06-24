# Task: Web UI integration + start_web.bat

## План

- [x] 1. Проанализировать структуру проекта, docker-compose.yml, start.bat
- [x] 2. Создать `docker-compose-web.yml` в `backend/service_checker/docker/` — полный аналог `docker-compose.yml` + frontend
- [x] 3. Создать `start_web.bat` в корне (автономный, без вызова start.bat, использует docker-compose-web.yml)
- [x] 4. Создать `reset_web.bat` в корне (остановка + удаление томов + пересборка docker-compose-web.yml)
- [x] 5. Финальная проверка: целостность, связи, актуализация readme
