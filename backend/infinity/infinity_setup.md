# Infinity Embedding Service — развёртывание

## docker-compose.yml (фрагмент)

```yaml
services:
  infinity:
    build:
      context: .
      dockerfile: Dockerfile.infinity
    image: rag-search-infinity:latest
    container_name: rag_search_infinity
    ports:
      - "7997:7997"
    volumes:
      - infinity_cache:/app/.cache
    command: >
      v2
      --model-id ${INFINITY_MODEL_ID:-Qwen/Qwen3-Embedding-0.6B}
      --port 7997
      --engine ${INFINITY_ENGINE:-torch}
      --device ${INFINITY_DEVICE:-cpu}
      --no-bettertransformer
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:7997/health || exit 1"]
      interval: 10s
      timeout: 10s
      retries: 30
      start_period: 1200s
    networks:
      - rag-net
    restart: unless-stopped

  postgres:
    image: pgvector/pgvector:pg16
    # ...

  rag-search:
    # ...
    depends_on:
      postgres:
        condition: service_healthy
      infinity:
        condition: service_healthy
```

Модель задаётся через переменную `${INFINITY_MODEL_ID}` (по умолчанию `Qwen/Qwen3-Embedding-0.6B`). Дефолт срабатывает, если переменная не задана в `.env`.

## Dockerfile.infinity

```dockerfile
FROM michaelf34/infinity:latest
RUN pip install --upgrade transformers sentence-transformers==5.1.0
```

## Переменные окружения (`.env` или `environment:`)

| Переменная | Назначение | Значение |
|---|---|---|
| `INFINITY_MODEL_ID` | ID модели на HuggingFace | `Qwen/Qwen3-Embedding-0.6B` |
| `INFINITY_ENGINE` | Бэкенд (`torch`, `optimum`, `ctranslate2`) | `torch` |
| `INFINITY_DEVICE` | Устройство (`cpu`, `cuda`, `mps`, `tensorrt`, `auto`) | `cpu` |

### Переменные rag_search_service

Эти переменные используются **не Infinity**, а сервисом `rag_search` для настройки провайдера эмбеддингов.

| Переменная | Назначение | Значение |
|---|---|---|
| `EMBEDDING_INSTRUCTION` | Инструкция для query-эмбеддингов (Qwen3). Пусто — без промпта | `""` |
| `EMBEDDING_MODEL` | Имя модели для запросов | `Qwen/Qwen3-Embedding-0.6B` |
| `EMBEDDING_DIM` | Размерность эмбеддинга | `1024` |
| `EMBEDDING_BASE_URL` | URL Infinity API | `http://infinity:7997` |
| `EMBEDDING_TIMEOUT` | Таймаут HTTP-запроса (сек) | `60` |

#### Инструкция для Qwen3-Embedding

Модель `Qwen3-Embedding` поддерживает промпты — инструкцию, которая добавляется перед текстом query для улучшения качества поиска. Задаётся в `.env` сервиса `rag_search`.

```env
# Без инструкции (по умолчанию) — работает для любых моделей
EMBEDDING_INSTRUCTION=

# С инструкцией — улучшает качество для Qwen3-Embedding
EMBEDDING_INSTRUCTION=Instruct: Дан поисковый запрос о технических стандартах, найди релевантные разделы документов\nQuery:
```

**Формат:** `{instruction}\n\n{query}` — инструкция и запрос разделяются двойным переводом строки.

**Работа без промпта:** Если `EMBEDDING_INSTRUCTION` пуст, `OpenAICompatibleProvider` отправляет текст в Infinity как есть — совместимо с любыми embedding-моделями.

## Важные замечания по развёртыванию

### Время запуска

**Первый холодный старт (build + загрузка модели): ~14 минут**

| Этап | Что происходит | Время |
|---|---|---|
| 1. Pull base image | `michaelf34/infinity:latest` (9,4 ГБ, сумма слоёв) | **~735s** |
| 2. pip install | `transformers` + `sentence-transformers==5.1.0` | **32s** |
| 3. Build image | Итого build | **795s (~13 мин 15 с)** |
| 4. Start container | После build | **~10s** |
| 5. Загрузка модели | Qwen3-Embedding-0.6B (~1 ГБ) скачивается с HF Hub при первом запуске Infinity | **Несколько минут** |

**Итоговое время от `docker-compose up -d infinity` до healthy: ~15–20 минут**

- healthcheck: `start_period: 1200s` (20 мин) — Docker не проверяет здоровье, пока модель качается и грузится
- После первого запуска модель кэшируется в volume `infinity_cache` — последующие старты **секунды**

### Занимаемое место

- Образ Infinity с доустановленными пакетами: **~9.4 ГБ**
- Кэш модели в volume: **~1 ГБ** (0.6B) или **~8 ГБ** (4B)
- После загрузки volume сохраняется между перезапусками — модель не качается заново

### Engine и Device

Параметры `--engine` и `--device` задаются через переменные `${INFINITY_ENGINE}` и `${INFINITY_DEVICE}`.

**Engine (бэкенд):**

| Значение | Когда использовать |
|---|---|
| `torch` | Универсальный: CPU, CUDA, MPS. Sentence-transformers модели |
| `optimum` | ONNX-модели с HuggingFace (рекомендованы для CPU, быстрее torch) |
| `ctranslate2` | Только BERT-модели, самый быстрый на CPU |

**Device (устройство):**

| Значение | Применение |
|---|---|
| `cpu` | Без GPU, универсально |
| `cuda` | NVIDIA GPU (требует nvidia-docker, `--gpus all`) |
| `mps` | Apple Silicon (M1/M2/M3) |
| `tensorrt` | NVIDIA GPU + TensorRT-образ Infinity (`latest-trt-onnx`) |
| `auto` | Автоопределение (предпочитает GPU если доступен) |

**Примеры:**

```bash
# CPU + ONNX (быстрее на CPU, требует ONNX-модели)
INFINITY_ENGINE=optimum INFINITY_DEVICE=cpu

# NVIDIA GPU
INFINITY_ENGINE=torch INFINITY_DEVICE=cuda

# Apple Silicon
INFINITY_ENGINE=torch INFINITY_DEVICE=mps
```

## Проблемы, с которыми столкнулись

### 1. `ImportError: cannot import name 'HfFolder'`

**Причина:** После обновления `transformers` ломается `sentence-transformers` (старая версия использует удалённый `HfFolder`).
**Исправление:** Закрепить `sentence-transformers==5.1.0` в Dockerfile.infinity:
```dockerfile
FROM michaelf34/infinity:latest
RUN pip install --upgrade transformers sentence-transformers==5.1.0
```

---

### 2. Health check не дожидается загрузки модели

**Проблема:** Стандартный `retries: 5` с `interval: 10s` даёт всего 50 секунд ожидания. Модель качается 15–25 минут.

**Исправление:**
```yaml
healthcheck:
  retries: 30          # 30 × 10s = 300s ожидания после start_period
  start_period: 1200s  # первые 20 мин — без проверок, модель качается
```
Docker ждёт 20 минут, затем начинает проверки. Суммарно ~25 минут на запуск.
