# Задача: починить диспетчеризацию full_ocr / OCR fallback в оркестраторе

## Симптом

Полный цикл (Upload → Preview → Approve → Full pipeline → Search) зависает.
Статус пайплайна: `full_ocr: running` — никогда не переходит в `completed`.
Celery-воркер не получает задачу, хотя шаг в БД помечен как `running`.

## Что уже починено (не трогать)

### Converter-validator — извлечение метаданных

**Файлы:**
- `backend/converter_validator_service/app/services/metadata_extractor.py`
- `backend/converter_validator_service/app/services/normalizer.py`

Добавлены regex-паттерны для всех типов документов: ГОСТ Р, ПКПС, ОСТ, РД, ТУ, НД, ISO, DNV, ASTM, СНиП/СП, чертежи.
`_find_doc_code` и `infer_source_type` теперь покрывают всё из `SOURCE_TYPE_TO_KEY`.
Добавлен fallback `_find_title` из имени файла.

**Тесты:** 64 шт, все проходят:
```bash
cd backend/converter_validator_service && python -m pytest tests/
```

---

## Что надо чинить: оркестратор — dispatch celery-задач

### Два места с багом

#### 1. OCR fallback после неудачного preview (`_run_ocr_fallback`)

**Файл:** `backend/orchestrator_service/app/core/pipeline/orchestrator.py`
**Функция:** `_run_ocr_fallback` (строка ~349)

Когда parser не смог извлечь текст из PDF (сканированный документ):
1. Converter preview возвращает `validated=False`
2. `_on_preview_completed` вызывает `_run_ocr_fallback`
3. Функция создаёт второй `preview_ocr` шаг (service="OCR Service") и вызывает `run_ocr_preview_step.delay(...)`
4. **Но celery-воркер не получает эту задачу** — в логах нет `Task tasks.pipeline.run_ocr_preview_step[...] received`

Проверить:
- Broker: `CELERY_BROKER_URL=redis://redis:6379/1` — достигает ли задача Redis?
- Queue: задача уходит в "pipeline"? Воркер слушает `-Q celery,pipeline,saga`
- Не падает ли `.delay()` с исключением (silent catch)?

#### 2. Full pipeline dispatch после approve (`approve_draft`)

**Файл:** `backend/orchestrator_service/app/core/pipeline/orchestrator.py`
**Функция:** `approve_draft` (строка ~844)

После одобрения черновика:
1. Создаётся шаг `full_ocr` (status=pending)
2. Стартует шаг (status=running): `start_task_step(full_step.id)`
3. Вызывается `run_parser_full_step.delay(...)` или `run_ocr_full_step.delay(...)`
4. **Но задача не доходит до celery** — нет `run_ocr_full_step[...] received` или `run_parser_full_step[...] received`

Проверить:
- `need_full_processing` — не `False` ли из-за `task.full_completed`?
- `full_step` — не `None` ли из-за несовпадения статуса?
- `.delay()` — не выбрасывает ли exception?

### Параллельная загрузка НД-документа

В логах видна параллельная загрузка документа `НД_№2_09_006...` (draft=4, task=4).
Его пайплайн **успешно прошёл** — значит dispatch РАБОТАЕТ для task 4.
Надо понять, чем task 3 отличается: возможно race condition, другая очередь,
или ошибка в логике `need_full_processing` / `use_parser_for_full`.

### Как воспроизвести

```bash
docker compose up -d --build converter-validator orchestrator celery-worker
python data/tests/test_load_pkps_pdf.py
# Ждать ~5 мин — пайплайн зависнет на full_ocr: running
```

Смотреть логи:
```bash
docker compose logs celery-worker | grep "task.*3"
docker compose logs orchestrator | grep -E "full_ocr|Enqueued.*3|Approving draft.*3"
```

### Ожидаемое поведение

- `run_ocr_preview_step.delay(3, 3, "f-d25314815ba8", ...)` достигает celery-worker
- OCR обрабатывает PDF, конвертер извлекает метаданные
- `run_parser_full_step.delay(3, 3, "f-d25314815ba8", ...)` достигает celery-worker
- Полный пайплайн завершается за ~2-3 мин

---

## Тесты после фикса

```bash
cd backend/converter_validator_service && python -m pytest tests/  # 64 шт
python data/tests/test_load_pkps_pdf.py  # полный E2E
```
