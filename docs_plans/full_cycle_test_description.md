# Full Cycle Integration Test — описание

**Цель**: Проверить сквозной пайплайн обработки документа в корневом docker-compose.yml
от загрузки PDF до поиска через RAG + Query.

---

## 1. Топология

```
User ──→ Gateway (:8080) ──→ Auth (:8082) ──→ Orchestrator (:8081)
                          ──→ Registry (:8084)
                          ──→ Parser (:8087)
                          ──→ Converter-Validator (:8086)
                          ──→ RAG Builder (:8090)
                          ──→ RAG Search (:8091)
                          ──→ Query (:8083) ──→ LLM (внешний)
```

## 2. Предусловия

### 2.1 Окружение
```bash
# Ключи
export ROUTERAI_API_KEY="sk-..."
# ИЛИ задать EMBEDDING_BASE_URL / EMBEDDING_API_KEY / LLM_API_URL отдельно

# .env в корне проекта (автоматически подхватывается docker compose)
EMBEDDING_BASE_URL=https://.../api/v1
EMBEDDING_API_URL=https://.../api/v1/embeddings
EMBEDDING_API_KEY=...
EMBEDDING_DIM=2048
VECTOR_DIMENSION=2048
EMBEDDING_MODEL=qwen/qwen3-embedding-8b
```

### 2.2 Подготовка
```bash
# Остановить service_checker (конфликтует с миграциями БД)
docker stop pkb-neuro

# Пересобрать и запустить корневой compose
docker compose up -d --build

# Дождаться готовности всех сервисов
docker compose ps  # все healthy
```

### 2.3 Тестовый файл
```bash
# PDF: backend/service_checker/pdf/7bd97d737317a8a272bb18a405ab2d04.pdf
# Это ГОСТ 10054-82 "Водостойкая абразивная шкурка" (123KB, 3 страницы)
```

## 3. Этапы теста

### Шаг 1. Аутентификация
```bash
TOKEN=$(curl -s -X POST "http://localhost:8082/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@example.com","password":"Admin1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```
**Ожидание**: `200`, в ответе `access_token`.

### Шаг 2. Создание черновика с PDF через Gateway
```bash
TS=$(date +%Y%m%d%H%M%S%N)
DRAFT=$(curl -s -X POST "http://localhost:8080/api/v1/drafts" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@backend/service_checker/pdf/7bd97d737317a8a272bb18a405ab2d04.pdf" \
  -F "document_key=test-${TS}" \
  -F "title=Test ${TS}" \
  -F "source_type=GOST")
DRAFT_ID=$(echo "$DRAFT" | python3 -c "import sys,json; print(json.load(sys.stdin)['draft_id'])")
TASK_ID=$(echo "$DRAFT" | python3 -c "import sys,json; print(json.load(sys.stdin)['task_id'])")
```
**Ожидание**: `202 Accepted`, поля `draft_id`, `task_id`, `status=uploaded`.

### Шаг 3. Подтверждение (approve)
```bash
APPROVE=$(curl -s -X PATCH "http://localhost:8080/api/v1/drafts/${DRAFT_ID}/decide" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"approve","comment":"Integration test"}')
DOC_ID=$(echo "$APPROVE" | python3 -c "import sys,json; print(json.load(sys.stdin)['document_id'])")
```
**Ожидание**: `200`, поля `document_id`, `version_id`.

### Шаг 4. Проверка документа в Registry
```bash
curl -s "http://localhost:8080/api/v1/registry/documents/${DOC_ID}" \
  -H "Authorization: Bearer $TOKEN"
```
**Ожидание**: `200`, тело с `data.id == ${DOC_ID}`.

### Шаг 5. Индексация через RAG Builder
```bash
BUILD=$(curl -s -X POST "http://localhost:8090/api/v1/rag/build" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"document_id\": ${DOC_ID},
    \"sections\": [{
      \"section_id\": 1,
      \"document_id\": ${DOC_ID},
      \"clause\": \"1\",
      \"level\": 1,
      \"path\": \"1\",
      \"page\": 1,
      \"type\": \"text\",
      \"content\": {\"text\": \"Текст документа для индексации\"}
    }]
  }")
STATUS=$(echo "$BUILD" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
```
**Ожидание**: `202 accepted`, `status == "indexed"`, `chunks_count > 0`.

### Шаг 6. Поиск через RAG Search
```bash
SEARCH=$(curl -s -X POST "http://localhost:8091/api/v1/rag/search" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Текст документа для индексации\",
    \"valid_at\": \"$(date +%Y-%m-%d)\",
    \"filters\": {\"document_ids\": [${DOC_ID}]}
  }")
COUNT=$(echo "$SEARCH" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('results',[])))")
SCORE=$(echo "$SEARCH" | python3 -c "
import sys,json; d=json.load(sys.stdin)
for r in d.get('results',[]):
    print(r['retrieval']['score'])
")
```
**Ожидание**: `200`, `results` не пуст, `score > 0`.

### Шаг 7. Чат через Query Service
```bash
SESSION=$(curl -s -X POST "http://localhost:8083/api/v1/chat/sessions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Integration test"}')
SESSION_ID=$(echo "$SESSION" | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")

curl -s -X POST "http://localhost:8083/api/v1/chat/sessions/${SESSION_ID}/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"content\": \"Query about GOST 10054-82\",
    \"attachments\": [{\"type\": \"document\", \"source_document_id\": ${DOC_ID}}]
  }"
```
**Ожидание**: `202 Accepted`, `status=pending`.

### Шаг 8. Проверка ответа
```bash
sleep 10  # дать время LLM
curl -s "http://localhost:8083/api/v1/chat/history?limit=1" \
  -H "Authorization: Bearer $TOKEN"
```
**Ожидание**: `200`, `status` не `failed`. Допустимо `not_found` (если контент не релевантен).

---

## 4. Известные проблемы и аномалии

| Проблема | Причина | Решение |
|----------|---------|--------|
| LLM 401 | Ключ не имеет прав на `/chat/completions` | Заменить API-ключ |
| RAG Builder 500 | Провайдер эмбеддингов недоступен/неверная размерность | Проверить EMBEDDING_* в .env |
| Conflict pkb-neuro | Service checker затирает миграцию БД (312→2048) | Остановить `pkb-neuro` |
| RAG Search не находит | Пулл документов не совпадает с запросом | Проверить контент секций и фильтр |

## 5. Структура теста в коде

Тест должен:
1. **Очистить БД** (опционально, если тест не idempotent)
2. **Проверить health** всех сервисов
3. **Выполнить шаги 1-8** последовательно
4. **Проверить ответы** на каждом шаге
5. **Зафиксировать метрики**: время каждого шага, статусы, размер ответа
6. **Очистить** созданные ресурсы (черновик, сессия) — опционально

```python
# Пример структуры теста (pytest + httpx)
class TestFullCycle:
    BASE = "http://localhost"
    PORTS = {"auth": 8082, "gateway": 8080, "rag_builder": 8090,
             "rag_search": 8091, "query": 8083}

    async def test_full_cycle(self):
        # 1. Auth
        token = await self.auth()
        # 2. Draft + PDF
        draft_id, task_id = await self.create_draft(token)
        # 3. Approve
        doc_id = await self.approve(token, draft_id)
        # 4. Registry check
        await self.check_registry(token, doc_id)
        # 5. RAG Builder index
        await self.index_document(token, doc_id)
        # 6. RAG Search
        results = await self.search(token, doc_id)
        assert len(results) > 0
        # 7. Query
        msg_id = await self.send_message(token, doc_id)
        # 8. Verify
        history = await self.get_history(token)
        assert history["status"] != "failed"
```

## 6. env-переменные для теста

| Переменная | Назначение | Fallback |
|-----------|-----------|----------|
| `EMBEDDING_BASE_URL` | Базовый URL эмбеддингов | `https://routerai.ru/api/v1` |
| `EMBEDDING_API_URL` | Полный URL эмбеддингов | `${EMBEDDING_BASE_URL}/embeddings` |
| `EMBEDDING_API_KEY` | Ключ для эмбеддингов | `${ROUTERAI_API_KEY}` |
| `EMBEDDING_DIM` | Размерность векторов | `2048` |
| `VECTOR_DIMENSION` | Размерность в БД | `${EMBEDDING_DIM}` |
| `EMBEDDING_MODEL` | Модель эмбеддингов | `qwen/qwen3-embedding-8b` |
| `LLM_API_BASE_URL` | Базовый URL LLM | `https://routerai.ru/api/v1` |
| `ROUTERAI_API_KEY` | Основной API-ключ | — |
