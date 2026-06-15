# TODO: Разложить Python-файлы по каталогам

## План
Корневые `.py` файлы (кроме `__init__.py`, `__main__.py`, `setup.py`) перенести в `core/`:
- `service_checker.py` → `core/service_checker.py` (дубль `__main__.py`, сделаем прокладку)
- `api_coverage_test.py` → `core/api_coverage_test.py`
- `pipeline_test.py` → `core/pipeline_test.py`
- `setup_db.py` → `core/setup_db.py`

## Шаги
- [x] 1. Создать todo.md (этот файл)
- [x] 2. Перенести `api_coverage_test.py` → `core/api_coverage_test.py` (move_path)
- [x] 3. Перенести `pipeline_test.py` → `core/pipeline_test.py` (move_path)
- [x] 4. Перенести `setup_db.py` → `core/setup_db.py` (move_path)
- [x] 5. Перенести `service_checker.py` → `core/service_checker.py` (move_path)
- [x] 6. Обновить импорты и пути во всех файлах проекта
- [x] 7. Обновить `readme.md` (структура проекта)
- [x] 8. Запустить тесты — 140 passed, 1 pre-existing fail (Docker integration)
- [x] 9. Финальная сверка по todo.md
