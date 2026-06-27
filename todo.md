# Задача: починить пайплайн загрузки → поиск ✅

## Статус: ВСЁ ИСПРАВЛЕНО И ПРОВЕРЕНО

### Что было починено

| № | Проблема | Корень | Фикс |
|---|----------|--------|------|
| 1 | Preview stuck `processing` | Дублирующиеся шаги в `_build_preview_status` | Уникализация по step_name + взятие лучшего статуса |
| 2 | `rag_index` оставался `pending` | `RAG_SERVICE_URL=http://rag-search:8091` перезаписывал `RAG_BUILDER_SERVICE_URL` | Убрал deprecated `RAG_SERVICE_URL` из `docker-compose.yml` |
| 3 | `run_rag_index_step()` падал с `unexpected keyword argument 'sections'` | Две Celery задачи с одинаковым именем `tasks.pipeline.run_rag_index_step` | Переименовал задачу в `pipeline_indexation.py` |
| 4 | Parser возвращал 0 sections для RAG | `full_parser_result.get("sections", [])` — парсер отдаёт `document.block[]`, а не `sections` | Трансформация block[] → Section[] для RAG Builder |
| 5 | RAG Builder 422 на sections | `section.document_id` = draft_id, а запрос шёл с registry document_id | Фикс document_id в секциях перед отправкой в RAG |
| 6 | RAG Builder 422 на document_id | `RagBuildRequest.document_id: str`, а RAG Builder ожидает int | Поменял тип на `int` |

### Результат теста

```bash
python data/tests/test_e2e.py

[PASS] ALL CHECKS PASSED
```

- Pipeline: ~15 сек
- Search: 150 total_found, тексты из PDF находятся
