# Не работает логин при start_web.bat

## Причина
Фронтенд настроен на `http://127.0.0.1:8081/api/v1` (порт Orchestrator), но маршруты `/auth/token` находятся в Gateway (порт **8080**). Запросы аутентификации уходят на Orchestrator, который не имеет auth-роутов → 404.

## Что сделано
- [x] 1. `UI-UX/UI Final/frontend/src/utils/http.ts` — `DEFAULT_GATEWAY_URL` изменён с 8081 → 8080
- [x] 2. `UI-UX/UI Final/frontend/src/components/DocumentRegistryPanel.tsx` — fallback изменён с 8081 → 8080
- [x] 3. `UI-UX/UI Final/frontend/README.md` — документация исправлена
- [x] 4. Проверено: других 8081 в source-коде фронтенда нет (grep по `*.ts, *.tsx, *.js, *.jsx` — 0 совпадений)
- [x] 5. Обновлены сопутствующие docs: `UI-UX/UI Final/README.md`, `UI-UX/README.md`, `UI-UX/UI Final/docs/first-run-ui-final-with-gateway.md`
- [x] 6. Корневой `README.md` — добавлено описание batch-файлов, портовой схемы и Gateway URL
