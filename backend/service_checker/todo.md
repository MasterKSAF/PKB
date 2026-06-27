# Todo: Docker-тесты в recheck.bat + отчёты

- [x] Прочитать все файлы

## 1. `docker.py` — _docker_run_gateway_tests()
- [x] Убрать `-m "not docker"` — запускать все тесты (в Docker-окружении)
- [x] Парсить вывод pytest (passed/failed/total) 
- [x] Изменить возврат с `bool` на `Dict` со статистикой

## 2. `reports.py` — _generate_full_report()
- [x] Добавить параметр `gateway_tests_result: Optional[Dict]`
- [x] Добавить секцию "🌐 Gateway Integration Tests"
- [x] Передать gateway_tests_result в общий статус

## 3. `cli.py` — cmd_docker()
- [x] Передать gateway_tests_result в _generate_full_report()

## 4. `recheck.bat` — шаг 7
- [x] Добавить шаг 7 после full-report
- [x] Запустить pytest, сохранить отчёт, вывести статистику

## 5. Тесты
- [x] Добавить тесты gateway-секции в отчёте
- [x] 17 тестов прошли (0 failures)

## 6. Проверка
- [x] Финальный перепросмотр — все изменения согласованы
- [x] Запуск тестов — 17 passed
- [x] guide.md обновлён (шаг 7 Gateway)
- [x] readme.md актуален (изменений не требуется)
- [x] `_docker_run_gateway_tests()` — 168 passed, 0 failed ✅
- [x] Отчёт gateway_tests.md — Summary корректный ✅
- [x] Секция Gateway в full_report — ✅ статус, статистика, ссылка
- [x] Исправлен отсутствующий импорт `GATEWAY_DIR` в `docker.py`
