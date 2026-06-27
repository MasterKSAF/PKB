# Проверка работоспособности query_service

- [x] Просмотр конфигурации LLM для query в корневом docker-compose
- [x] Запуск тестов query_service — 85 passed
- [x] Проверка LLM клиента и моков
- [x] Диагностика проблемы: модель `deepseek/deepseek-v4-flash` не принимается opencode.ai
- [x] Исправление: вынесена в переменную `${LLM_MODEL:-...}` для query и `${DEFAULT_LLM_MODEL:-...}` для converter
- [x] В `.env` заданы локальные значения: `LLM_MODEL=deepseek-v4-flash`, `DEFAULT_LLM_MODEL=deepseek-v4-flash`
- [x] Проверка: LLM вызов через query сервис — **200 OK, ответ получен**
