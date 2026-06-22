# Исправление full_report.md

## Проблемы
1. Статистика по API не выводилась в сводной таблице (только иконка, без чисел)
2. Таблица по оркестратору вылезла выше, чем таблица пайплайнов по сервисам
3. Coverage падал на Gateway draft → пустой API Coverage
4. Дублирование секции Orchestrator Pipelines с Pipeline Testing детализацией

## План
- [x] Поменять местами секции 1a (Orchestrator Pipelines) и 1b (Pipeline статусы по сервисам)
- [x] Добавить числовую статистику по API в сводную таблицу (passed/total/failed)
- [x] Исправить pre-prepare Gateway draft — заменить JSON на form-data, убрать RuntimeError
- [x] Удалить дублирующуюся секцию Orchestrator Pipelines
- [x] Обновить тесты — 12 passed
