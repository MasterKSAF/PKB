# Fix: 6-польный бизнес-ключ для детекции дублей

## B1 — schema + client + mock
- [x] 1.1 Добавить `title_hash_sha256: Optional[str]` в `CheckUniquenessRequest`
- [x] 1.2 Обновить `check_uniqueness()` — принимать и передавать `title_hash_sha256`
- [x] 1.3 Скорректировать mock_response в `check_uniqueness()` — возвращать `title_hash_sha256`

## B2 — Исправить _mock_check_uniqueness
- [x] 2.1 Заменить сравнение `document_key == title` на проверку `title_hash_sha256`
- [x] 2.2 Вернуть `title_hash_sha256` в ответе мока

## B3 — create_draft endpoint
- [x] 3.1 Вычислять 6-польный `title_hash_6field` по формуле
- [x] 3.2 Вычислять правильный `title_key` (6-польный) — поле `okstu_code` вместо `jurisdiction`
- [x] 3.3 Передавать `title_hash_6field` в `check_uniqueness()`
- [x] 3.4 Сохранить `title_hash` (SHA-256(title)) для обратной совместимости в DraftCreateResponse

## B4 — Тесты
- [x] 4.1 `test_check_uniqueness` — добавить `title_hash_sha256` в параметры
- [x] 4.2 `test_check_uniqueness_duplicate` — проверить `is_duplicate=True` при совпадении хеша
- [x] 4.3 `test_drafts_boundaries.py` — E2E-тест: две загрузки с одинаковыми metadata → `is_duplicate_document=True`
- [x] 4.4 `test_drafts.py` — обновить тесты title_key под новую формулу

## B5 — Финальные проверки
- [x] 5.1 Прогнать тесты — 701 passed, 2 skipped, 1 xfailed
- [x] 5.2 Финальный обзор правок
