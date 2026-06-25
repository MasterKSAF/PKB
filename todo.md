# Диагностика "Поиск временно недоступен"

## Выполнено
- [x] Проверен diagnostics endpoint (`/api/v1/system/diagnostics?verbose=true`)
- [x] Проверены сервисы напрямую: infinity (7997), rag-search (8091), query (8083), registry (8084)
- [x] Установлена корневая причина: OOM kill infinity_emb
- [x] Прочитан код pipeline.py — точка возникновения ошибки
- [x] Прочитан код diagnostics.py — `run()` не возвращал stderr
- [x] Прочитан конфиг infinity в docker-compose.yml
- [x] Прочитан issue michaelfeil/infinity#579 — optimum engine жрёт >10GB при загрузке
- [x] Добавить memory limit infinity в docker-compose.yml
- [x] Сменить engine optimum → torch и модель ONNX → BAAI/bge-reranker-v2-m3
- [x] Починить diagnostics.py — `run()` возвращает stderr при ошибке (проверено локально)
- [x] Записать в specificity.md диагностику и выводы
- [x] Записать в guide.md правила диагностики
- [x] Финальный обзор
