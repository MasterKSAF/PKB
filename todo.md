# Текущая сессия: проверка загрузки pdf_check + очистка по флагу + анализ дублей

## 1. Модифицировать `data/tests/config.py`
- [x] `ensure_services()` — убрать полную пересборку, только очистка по флагу
- [x] Добавить `TEST_CLEANUP` (true/false, default true) — управление очисткой БД/Minio
- [x] `TEST_SKIP_REBUILD=true` сохранён для обратной совместимости

## 2. Модифицировать `data/tests/test_pdf_tests_full.py`
- [x] Сделать директорию параметризуемой (по умолчанию pdf_tests, можно pdf_check)
- [x] Учесть auto-approve (проверка статуса task до вызова decide)
- [x] 409 для approve трактуется как "уже решено"

## 3. Запустить загрузку data/pdf_check
- [ ] `TEST_CLEANUP=false python data/tests/test_pdf_tests_full.py data/pdf_check`
- [ ] Проверить корректность, параллельность, auto-approve

## 4. Анализ дублей в БД
- [ ] SQL-запрос к postgres: дубли в registry.documents, pipeline.tasks
- [ ] Определить причину появления
