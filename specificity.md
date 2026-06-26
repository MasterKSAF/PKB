# Specificity — аномалии и трудные моменты

## ⚙ Особенности рабочего окружения

### G4. Diagnostics на сервере — docker логи недоступны

Gateway имеет встроенный diagnostics-модуль (`diagnostics.py`) с эндпоинтами:
- `GET /api/v1/system/diagnostics` — краткая сводка (публичный)
- `GET /api/v1/system/diagnostics?verbose=true` — полная (диски, порты, Docker, логи, dmesg)
- `GET /api/v1/system/diagnostics/{service}` — детально по сервису (name: query, auth, rag-search...)
- `GET /api/v1/system/diagnostics/system` — логи ядра (dmesg) и memory pressure

**Важно:** diagnostics вызывает `docker inspect`, `docker logs`, `docker ps` через subprocess внутри контейнера gateway. Раньше `run()` возвращал только stdout, stderr подавлялся — из-за этого ошибки docker не отображались. **Исправлено:** `run()` теперь возвращает stderr при ошибке, diagnostics показывает реальную причину (`error: no such object: pkb-query`, `Error response from daemon`).

**Что работает всегда (без docker):** dmesg, journalctl, memory pressure, df, free, ss — через `/host/proc`.

**Как диагностировать сервисы на сервере без SSH:**
1. `GET /api/v1/system/diagnostics?verbose=true` — увидеть OOM в dmesg
2. `GET /api/v1/system/diagnostics/{service}` — пытается взять docker logs, но если docker не работает — будет пусто
3. Нужен SSH на сервер для `docker logs pkb-query --tail 50`

### G5. Infinity OOM — диагностика и схема отказа (26.06)

**Симптом:** фронтенд: «Поиск временно недоступен».

**Схема отказа:**
```
infinity (7997) — OOM kill
  ↓
RAG search (8091) — timeout (зависит от infinity)
  ↓
query_service.pipeline.run_pipeline()
  → rag_client.search() 3 retries × 30s timeout → всё падает
  → запись в БД: status="failed", content="Поиск временно недоступен..."
```

**Диагностика (через gateway diagnostics):**
- `GET /api/v1/system/diagnostics?verbose=true` → dmesg показывает OOM kill infinity_emb
- `GET /api/v1/system/diagnostics/query` → пусто (docker не работает внутри контейнера)
- `GET /api/v1/system/diagnostics/system` → dmesg + memory pressure
- Прямые запросы к infinity:7997, rag-search:8091 → timeout (порты не открыты наружу)

**Причина:** infinity без `mem_limit` грузит `bge-reranker-v2-m3-ONNX` через optimum engine и жрёт ~30GB RAM. На сервере 32GB RAM + 4GB swap. Своп исчерпан, OOM убивает infinity, после перезапуска infinity снова забирает всю память и система в цикле OOM.

**Фикс (в docker-compose.yml):**
- `mem_limit: 8g`, `memswap_limit: 0` — не даёт infinity убить всю систему
- `--engine torch` вместо `--engine optimum` — optimum при загрузке ONNX создаёт временные буферы >10GB (см. [michaelfeil/infinity#579](https://github.com/michaelfeil/infinity/issues/579))
- `--model-id BAAI/bge-reranker-v2-m3` (PyTorch) вместо `onnx-community/bge-reranker-v2-m3-ONNX` — torch engine не загружает ONNX
- `--batch-size 1` — снижает пиковое потребление

**Выводы:**
- Diagnostics gateway не может читать docker logs (docker CLI отсутствует внутри контейнера gateway или не смонтирован сокет).
- Единственный источник диагностики без SSH — dmesg (через /host/proc) и health endpoints.
- При добавлении нового сервиса с потенциально высоким потреблением памяти — обязательно указывать `mem_limit`.
- При OOM одного сервиса валится вся цепочка downstream. Нужен Resilience: circuit breaker на rag_client.

### G6. FastAPI трейлинг-слеш — 307 redirect ломает прокси через Gateway

**Проблема:** Если роут FastAPI определён с `"/"` (слеш), а клиент шлёт запрос без слеша — FastAPI отвечает 307 с Location на внутренний Docker-hostname (напр. `http://orchestrator:8081/api/v1/drafts/`). Браузер не может резолвить Docker-имена и падает с `ERR_NAME_NOT_RESOLVED`.

**Где проявилось:** `POST /api/v1/drafts` в оркестраторе — роут был `@router.post("/")`, нужно `@router.post("")`.

**Фикс в Gateway (client.py):** перехват 3xx ответов и замена Location с внутреннего URL на Gateway (`proxy_request`).

**Профилактика:**
- Определять роуты без слеша — `@router.post("")`, а не `@router.post("/")`
- При добавлении нового сервиса проверить, не утекают ли внутренние URL наружу
