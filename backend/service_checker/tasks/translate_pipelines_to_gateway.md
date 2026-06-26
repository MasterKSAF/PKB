# Задача: перевести все пайплайны на Gateway

## Контекст

Сейчас пайплайны в `backend/service_checker/pipelines/` ходят напрямую в сервисы (orchestrator:8081, registry:8084, auth:8082 и т.д.).
Нужно перевести их на Gateway (порт 8080), чтобы тестировалась реальная цепочка через единую точку входа.
Прямые вызовы сервисов остаются только в API-тестах покрытия (`ApiCoverageTester`).

Уже сделан пример — `orchestrator_draft_lifecycle.py` полностью переведён на Gateway.

## Что нужно сделать

Для каждого файла в `backend/service_checker/pipelines/` (кроме уже переведённого `orchestrator_draft_lifecycle.py`):

1. Поменять `services = [...]` на `services = ["gateway"]`
2. В каждом `PipelineStep(...)` заменить:
   - `service="..."` на `service="gateway"`
   - `port=XXXX` на `port=8080`
   - Если есть явный порт в аргументах — удалить/заменить на `port=8080`
3. Auth-шаги: path `/api/v1/auth/token` остаётся тем же (Gateway проксирует)
4. Registry-шаги: пути `/api/v1/registry/*` остаются (Gateway проксирует)
5. MinIO-шаги: MinIO (S3) **не идёт через Gateway** — MinIO остаётся прямым вызовом на порт 19000. Gateway не проксирует S3.
   - MinIO-шаги оставить с `service="minio"` и `port=19000`
6. Проверить, что `services` список не включает minio (minio остаётся прямым)

## Список файлов (14 шт)

| Файл | Сервисы сейчас | MinIO? |
|------|---------------|--------|
| `admin_user_lifecycle.py` | auth, query | нет |
| `chat_inference.py` | auth, query, rag_search | нет |
| `document_approval.py` | auth, orchestrator, registry, rag_builder, rag_search | нет |
| `document_processing.py` | auth, minio, parser, converter_validator, registry, rag_builder, rag_search | **да** |
| `full_document_lifecycle.py` | auth, registry, rag_builder, rag_search | нет |
| `multi_document_cross_search.py` | auth, minio, parser, converter_validator, registry, rag_builder, rag_search | **да** |
| `orchestrator_document_reject.py` | auth, orchestrator | нет |
| `orchestrator_document_reprocess.py` | auth, orchestrator, registry | нет |
| `orchestrator_document_versions.py` | auth, orchestrator, registry | нет |
| `orchestrator_draft_delete.py` | auth, orchestrator | нет |
| `orchestrator_full_document_lifecycle.py` | auth, orchestrator, registry, rag_builder, rag_search | нет |
| `orchestrator_metadata_update.py` | auth, orchestrator | нет |
| `registry_lifecycle.py` | auth, registry | нет |
| `registry_quarantine.py` | auth, registry | нет |

## Пример (уже сделано)

См. `orchestrator_draft_lifecycle.py` — как должны выглядеть шаги после перевода.

## Тесты

После изменений нужно обновить соответствующие тесты в `tests/test_pipeline_*.py`:
- `test_pipeline_attributes`: `assert "gateway" in p.services`
- `test_build_steps_order`: обновить имена шагов (добавить "(через Gateway)")
- `test_*`: заменить `assert step.service == "orchestrator"` на `"gateway"`
- Добавить `test_all_steps_use_gateway` — проверить что все шаги через gateway (кроме minio)
- Добавить `test_draft_creation_path_no_trailing_slash` если есть POST /drafts

## Проверка

reckeck.bat проходит все проверки на докере
