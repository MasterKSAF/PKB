# Сверка проекта с документацией

## Выполнено ✅

### README.md (vs фактическая структура)
- [x] **Неполный список docs/**: добавлены mock_architecture.md, db_diagrams.md, diagrams.md, pipeline-файлы, JSON-схемы
- [x] **Неполный список mocks/tests/**: добавлены все 8 файлов
- [x] **Устаревшее количество тестов**: обновлено 496 → 530+
- [x] **Не описаны mocks/__init__.py, mocks/requirements.txt, mocks/todo.md** — добавлены

### guide.md (не существует)
- [x] **guide.md создан** — архитектурные решения и ориентиры

### run_all.py (сломан)
- [x] **run_all.py исправлен** — теперь запускает единый mock-gateway (`mocks.gateway:app`)

### Пустые папки-остатки
- [x] **Удалены** mocks/auth_service/, mocks/orchestrator_service/, mocks/query_service/, mocks/registry_service/

### .rules
- [x] **Синхронизировать readme.md → README.md** в .rules п.2.1

---

## Финальная проверка
- [x] Протестировать run_all.py — импорт mocks.gateway OK, gateway.main OK
- [x] Проверить целостность связей (gateway/, mocks/, docs/, tests/) — все 100% на месте
- [x] Запущены тесты: 22/22 rate_limiting, 34/34 health+routing — все OK
- [x] Найден и исправлен **`mocks/tests/start_service.py`** — импортировал удалённые модули
- [x] Найден и исправлен устаревший раздел «Быстрый старт» в README — команды запуска отдельных сервисов
- [ ] **Не требует правок**: specificity.md — аномалии релевантны
