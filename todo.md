# Сессия 30.06 — Infinity reranker, таймауты, 404 валидации

- [x] InfinityRerankerProvider — новый провайдер под Infinity v2 (relevance_score, document)
- [x] Фабрика провайдеров — автоопределение по URL
- [x] REGISTRY_SERVICE_URL — исправлен двойной /api/v1 у converter-validator
- [x] EMBEDDING_TIMEOUT разделён: rag-search=10, rag-builder=120
- [x] RERANKER_FETCH_MULTIPLIER=2 (20 кандидатов вместо 500)
- [x] GATEWAY_REQUEST_TIMEOUT=300
- [x] Timeout в тесте увеличен до 120с
- [x] Проверка PDF — 5 файлов, 3 текстовых (8/8 verified)
- [x] Фиксация аномалий в specificity.md

**Не исправлено:**
- Документы остаются в validating (архитектурное решение)
