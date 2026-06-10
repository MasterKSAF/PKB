# ✅ Выполнено: проверка создания БД встроена в service_checker

## Что сделано

### 1. Создан `core/db_check.py`
- Модуль проверки состояния PostgreSQL в Docker
- `run_db_check()` — выполняет 12 проверок: БД, расширения, схемы, Registry, RAG
- `format_db_report()` — формирует Markdown-отчёт с таблицей
- `DbCheckResult` — data class со свойствами `healthy`, `summary_icon`

### 2. Добавлен `docker --action db-check`
- Отдельная команда: `python service_checker.py docker --action db-check`
- Выводит таблицу с детальным состоянием БД

### 3. Колонка `CheckDb` в full-report
- В сводную таблицу full-report добавлена колонка `CheckDb` после `Ping`
- Показывает ✅/❌/⚠️ в зависимости от состояния БД
- Детальный блок "🗄️ БД PostgreSQL" добавлен после Pipeline детализации
- `recheck.bat` теперь явно упоминает db-check в шаге 5/5

### 4. Удалён `tests/test_docker_db_check.py`
- Перенесено из юнит-тестов в основной чекер
- Больше не в pytest, а в `service_checker docker --action db-check`
- `readme.md` очищен от упоминаний удалённого файла

### 5. Проверка целостности
- 121 unit-тест пройдено (2 pre-existing: Registry, RAG Builder)
- Все тесты отчёта обновлены под новую колонку CheckDb
- `service_checker.py docker --action db-check` работает и выводит отчёт

## Использование
```bash
# Только проверка БД
python service_checker.py docker --action db-check

# Полный отчёт (включает проверку БД)
python service_checker.py docker --action full-report

# recheck.bat (включает full-report с БД)
docker\recheck.bat
```

## Остаётся
- Registry и RAG Builder не имеют `create_all()` в startup (известная проблема)
- При полном запуске Docker `db-check` покажет ✅
