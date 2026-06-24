
# Приведение SERVICE_URL к единому формату — выполнено

## Что сделано
- [x] **`docker-compose.yml`**: `x-env-service-urls` — все URL теперь без `/api/v1` (REGISTRY, VALIDATE, RAG_BUILDER, RAG_SEARCH, RAG_SERVICE). Из gateway убрано переопределение `REGISTRY_SERVICE_URL`.
- [x] **`orchestrator_service/config.py`**: `RAG_BUILDER_SERVICE_URL` и `RAG_SEARCH_SERVICE_URL` — без `/api/v1`.
- [x] **`orchestrator_service/rag_client.py`**: endpoints с `/api/v1` (`/api/v1/rag/build`, `/api/v1/rag/search`...).
- [x] **`query_service/config.py`**: `RAG_SERVICE_URL` — без `/api/v1`.
- [x] **`query_service/rag_client.py`**: путь с `/api/v1/rag/search`.
- [x] **Тесты**: обновлены, 34/34 прошли, регрессия 315/321 (те же 6 pre-existing).
