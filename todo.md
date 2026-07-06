# Задача: Исправить 500 ошибку при загрузке документов

## Текущее состояние
- UI на localhost:3300 не может загрузить документы, получает 500 ошибка
- В логах orchestrator: `FOR UPDATE is not allowed with aggregate functions`
- Запрос: `SELECT count(...) ... FOR UPDATE` запрещён в PostgreSQL

## Анализ
**Корневая причина**: метод `count_active_tasks` в `app/repositories/pipeline.py` (строка ~53-63) делает `SELECT count(...) FOR UPDATE`, что запрещено в PostgreSQL. PostgreSQL не позволяет комбинировать агрегатные функции (count, sum и т.д.) с `FOR UPDATE`.

**Где вызывается**: `start_pipeline` → `count_active_tasks(for_update=True)` на строке 390 в `orchestrator.py`.

## План
1. Исправить `count_active_tasks` — при `for_update=True` сначала выбирать ID с `FOR UPDATE`, потом считать
2. Проверить, что `try_activate_next_queued_task` тоже не использует count+FOR UPDATE
3. Проверить тесты, которые покрывают этот код
4. Протестировать исправление
