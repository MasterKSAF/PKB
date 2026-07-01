# Todo — Чаты не отображаются после F5 (01.07)

### Сделано
- [x] **Диагностика**: проблема найдена — query service возвращает проекты без вложенных сессий (чатов)
- [x] **schemas.py**: добавлена схема `ProjectSessionItem`, поле `sessions` в `ProjectListItem`
- [x] **projects.py**: `list_projects` загружает сессии через `selectinload(ChatProject.sessions)` и возвращает их в ответе

### Осталось (на сервере)
- [ ] Пересобрать query service: `docker compose up -d --build query`
- [ ] Проверить, что `GET /api/v1/chat/projects` возвращает сессии внутри проектов
- [ ] Либо деплой через `./deploy.sh`
