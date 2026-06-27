# Задача следующему агенту: починить пайплайн загрузки → поиск

## Суть

Полный цикл (Upload → Preview → Approve → Full pipeline → Search) не проходит.
Нужно: загрузить PDF из `data/pdf/`, дождаться обработки, найти строку из документа через `POST /rag/search`.

## Два блокера

### 1. Preview status не приходит в completed

`_build_preview_status` в `backend/orchestrator_service/app/api/v1/endpoints/drafts.py`
— из-за дублирующихся шагов `preview_converter` (один completed, второй pending).
Фикс: уникализировать шаги или проверять `any` вместо `all`.

### 2. RAG-индексация висит

После `registry_creation` шаг `rag_index` остаётся `pending`.
Нужно разобраться с дублированием шагов в `approve_draft`
(`backend/orchestrator_service/app/core/pipeline/orchestrator.py`)
и убедиться что `run_rag_index_step.delay()` диспатчится при `registry_creation` completed.

## Что уже починено (не трогать)

| Файл | Что сделано |
|------|------------|
| `gateway/client.py` | Убран transform у rag route (обрезал `/rag/`) |
| `orchestrator/.../drafts.py` | `year` обёрнут в `str()` |
| `orchestrator/.../orchestrator.py` | `version_id` вынесен до if/elif; добавлен шаг rag_index; новый elif для rag_index |
| `orchestrator/.../pipeline_formation.py` | parser_full ждёт результат; converter_full передаёт raw_json; добавлен `run_rag_index_step` |
| `orchestrator/.../parser_client.py` | get_status URL исправлен; добавлен get_result |

## Тесты

В `data/tests/` лежат:
- `test_full_pipeline.py` — полный цикл (много выводов, недоделан)
- `test_quick.py` — сокращённый 
- `test_go.py` — минимальный (сейчас не проходит из-за блокеров)

После фиксов нужно создать `data/tests/test_e2e.py` с коротким чистым тестом:
1. Загрузить PDF
2. Preview (без ожидания completed)
3. Approve
4. Ждать full pipeline (≤30 сек)
5. Искать строку из документа
6. Проверить что результат содержит искомое

## Проверка

```bash
docker compose up -d --build orchestrator celery-worker
python data/tests/test_go.py
# Должно: Search → результаты с искомым текстом
```
