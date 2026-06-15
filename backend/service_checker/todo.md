# service_checker: согласование настроек между rag_builder и rag_search

## 1. Эмбеддинги (выполнено)
- supervisord: `EMBEDDING_API_URL`, `VECTOR_DIMENSION` для rag-builder
- entrypoint: все `EMBEDDING_*` переменные + `VECTOR_DIMENSION` в .env
- recheck.bat / recheck.sh: не трогать postgres/redis — только дроп схем
- Файлы отчётов: фиксированные имена без дат

## 2. JWT токен (выполнено)
- supervisord: `JWT_SECRET_KEY`, `JWT_ALGORITHM` для rag-builder
- entrypoint: `JWT_SECRET_KEY`, `JWT_ALGORITHM` в .env rag_builder_service и auth_service
- RAG Builder service def: depends_on + auth, warning о разных JWT_SECRET_KEY

## Файлы
- [x] `docker/supervisord.conf` — EMBEDDING_API_URL, VECTOR_DIMENSION, JWT_SECRET_KEY, JWT_ALGORITHM для rag-builder
- [x] `docker/entrypoint.sh` — .env: EMBEDDING_* + VECTOR_DIMENSION + JWT_*
- [x] `docker/recheck.bat` — не убивать pg/redis, дроп схем + flush redis
- [x] `docker/recheck.sh` — синхронизирован с recheck.bat
- [x] `core/cli.py` — фиксированные имена отчётов
- [x] `core/docker.py` — фиксированные имена отчётов, убран timestamp
- [x] `services/rag_builder.py` — depends_on + auth, warning о JWT
- [x] `specificity.md` — п.27 (эмбеддинги), удалён устаревший п.7.7

## Проверка
- [ ] Перезапустить через recheck.bat и убедиться что rag_builder build проходит без 401
