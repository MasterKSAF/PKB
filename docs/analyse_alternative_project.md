# Анализ альтернативного проекта Knowledge Base (MVP)

> Сравнение с текущей архитектурой PKB Neuroassistant и рекомендации.
> Учтены уточнения от 13.06.

Дата анализа: 13.06.2026  
Источник: Технический проект «Реализация модуля Knowledge Base (MVP)» (ПКБ «Петробалт», v1.1–1.4)

---

## 1. Детальный разбор по пунктам

### 1.1. Граф связей (document_references)

**Текущее состояние:**
- Таблица `registry.document_references` существует в ER-диаграмме.
- Поля: `source_document_id`, `target_doc_code`, `reference_type`, `context`, `current_status`, `replaced_by`, `replacement_date`, `is_resolved`, `resolved_document_id`.
- Извлечение ссылок — в Converter-validator (поле `cross_references` в ответе).
- Сохранение — в Registry (шаг 3.3 Pipeline 1).
- **Проблема:** `is_resolved` всегда `FALSE`, потому что нет механизма, который проставляет `resolved_document_id`.

**Отличие от альтернативы:** Альтернативный проект описывает явный периодический резолвер с частичным индексом `WHERE is_resolved = FALSE`. У нас эта логика не специфицирована.

**Рекомендация:**
Добавить в документацию спецификацию резолвера:

```
### Резолвер графа связей (module: registry-service / background task)

Назначение: сопоставить target_doc_code с registry.documents.doc_code
и проставить resolved_document_id.

Триггеры:
  - По событию: при создании нового документа в registry.documents,
    выполнить UPDATE всех is_resolved = FALSE, где target_doc_code = new_doc.doc_code.
  - Фоново: CRON-задача (например, каждый час) для обработки оставшихся ссылок.

SQL:
  UPDATE registry.document_references AS ref
  SET is_resolved = TRUE, resolved_document_id = d.id
  FROM registry.documents AS d
  WHERE d.doc_code = ref.target_doc_code
    AND ref.is_resolved = FALSE;

Индекс:
  CREATE INDEX idx_refs_unresolved 
  ON registry.document_references(target_doc_code) 
  WHERE is_resolved = FALSE;
```

**Важно:** нормализатор `doc_code` должен быть единым — как при сохранении `registry.documents.doc_code`, так и при извлечении `target_doc_code` в Converter-validator. Иначе совпадения не будет.

---

### 1.2. Repromote (переиндексация)

**Текущее:** В пайплайне 2 (RAG Builder) есть эндпоинт `DELETE /rag/build/{doc_id}` для удаления чанков документа. Документ — неизменяемый (immutable), переиндексация возможна только при выходе новой версии файла.

**Корректировка (с учётом архитектуры):**
Repromote — это **не удаление документа**, а **перестроение чанков** для существующего документа. Это фоновая задача, у неё не может быть единой транзакции на всё.

```
### Процесс переиндексации (RAG Builder)

Триггер: выход новой версии документа (document_versions), либо ручной
запрос администратора.

Шаги:
1. Scheduler (15 мин) → POST /rag/build (document_id, version_hash)
2. RAG Builder → статус документа processing_status = 'indexing'
3. DELETE FROM rag.document_chunks WHERE document_id = $1
4. Генерация новых чанков + эмбеддингов
5. INSERT новых чанков в rag.document_chunks
6. UPDATE registry.documents SET processing_status = 'indexed'

Защита:
- Пока processing_status = 'indexing', RAG Search исключает документ
  из поиска (WHERE d.processing_status = 'indexed').
- При сбое: старые чанки удалены, новые не созданы. Статус → 'failed'.
  Требуется повторный запуск.
- Идемпотентность: DELETE перед INSERT исключает дубли.
```

---

### 1.3. Управление размерностью эмбеддингов

**Текущее:** `VECTOR(1536)` — размерность OpenAI/text-embedding-ada-002.

**Корректировка:** Это **функционал RAG Builder**, а не DDL-операция. Смена модели эмбеддингов — это процесс переиндексации всех документов в системе.

```
### Смена модели эмбеддингов (RAG Builder)

Сценарий:
1. Администратор меняет конфигурацию RAG Builder:
   - новая модель (например, multilingual-e5-large, 768)
   - новая стратегия чанкинга (опционально)

2. RAG Builder выполняет:
   ALTER TABLE rag.document_chunks 
   ALTER COLUMN embedding TYPE VECTOR(new_dim);

   Это пересоздаёт HNSW-индекс под новую размерность.

3. Запускает полную переиндексацию всех документов:
   - Чтение секций из registry.document_sections
   - Чанкинг
   - Вычисление эмбеддингов новой моделью
   - UPDATE rag.document_chunks SET embedding = ...

Инструкция по смене фиксируется в документации RAG Builder.
```

---

### 1.4. Постобработка LLM

**Текущее:** В пайплайне 3 есть этап «Обогащение цитирований». Валидация ссылок не описана.

**Это функционал Query Service** — можно добавить в `query_service_api.md` или `pipeline3-search.md` на согласование.

```
### Постобработка ответа LLM (Query Service)

После получения ответа от LLM выполняется:

1. Валидация цитирования:
   - Поиск ссылок вида [ГОСТ ХХХХ-ХХ, п. X.X]
   - Сверка с переданным контекстом (sources[].doc_code + .clause)
   - Если ссылка не найдена в контексте → удалить или пометить
     citation_verified: false

2. Извлечение таблиц:
   - Если LLM вернула таблицы в markdown → преобразовать в JSON
     для удобства отображения в UI

3. Оценка confidence:
   - На основе RRF-скоров чанков + процент подтверждённых ссылок
   - Включается в финальный JSON-ответ

Статус: на согласование с командой.
```

---

### 1.5. Multi-tenancy

В альтернативном проекте есть `tenant_id TEXT NOT NULL DEFAULT 'default'` в `nsi.chunks` — изоляция на уровне строки БД.

**Для PKB Neuroassistant на MVP это не требуется:**
- Система внутренняя для ПКБ «Петробалт».
- Изоляция реализована на уровне приложения — через `chat.projects` + `auth.users` + RBAC.
- Изоляция на уровне данных (tenant_id) потребуется, если систему будут внедрять в нескольких организациях с общей БД. Это перспектива, не для MVP.

Отдельной задачи не требуется.

---

### 1.6. Классификаторы

**Текущее состояние:**
- `docs/specifications/classifier_roots.csv` — 4 корневых узла.
- `docs/specifications/mks_oks_classifier.csv` — ~500 строк, весь справочник МКС/ОКС.
- Ссылка из API-документации: `registry_service_api.md` (группа classifiers, L87-88).

**Всё корректно.** CSV-файлы на месте, формат совпадает с альтернативным проектом по структуре (classifier_system, code, parent_code, full_name, level/status). Дополнительных действий не требуется.

---

## 2. Резюме: что НЕ актуально из первого анализа

| Пункт из первой версии | Решение |
|------------------------|---------|
| Размерность эмбеддингов (1536 vs 768) | Выбор модели — за командой. Зафиксирован как функционал RAG Builder (п. 1.3) |
| Структурированный ответ API (tables/figures/confidence) | Часть постобработки LLM (п. 1.4) |
| Параметры LLM и системный промпт | На усмотрение команды — производственная настройка |
| Расширение контекста через ltree | На усмотрение команды — может быть реализовано в Query Service |
| Отдельные таблицы для формул | В текущей архитектуре всё в JSONB, решение осознанное |
| ENUM relation_type | Не требуется — current_type 'single'/'range' достаточно |
| Таблица promotion_history | Не требуется — историю заменяет registry.document_history |
| Разделение на purgatory/nsi | Концептуально интересно, но перестройка не требуется |

---

## 3. Что добавить в документацию

| Файл | Что добавить |
|------|-------------|
| `api/registry_service_api.md` | Спецификацию резолвера графа связей (группа references) |
| `api/rag_builder_service_api.md` | Описание переиндексации и смены модели эмбеддингов |
| `pipelines/pipeline3-search.md` | Постобработку LLM (валидация цитирования) — на согласование |
