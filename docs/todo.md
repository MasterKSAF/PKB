# Todo: Адаптация опыта Purgatory (13.06)

## Решение
Взять в текущую документацию следующие решения из технического проекта Purgatory:

---

## План работ

### 1. Блок: Нормализатор — новый раздел документации

Создать `docs/specifications/normalizer_specification.md`

**Что включить:**
- Общее назначение: дедупликация, бизнес-ключ, нормализация названий
- Формула бизнес-ключа: `SHA-256(era | source_type | mks | okstu | doc_code | normalized_title)`
- Алгоритм нормализации названия:
  - Приведение к нижнему регистру, замена ё→е
  - Сверка с терминологическим реестром (terminology_registry)
  - Детект латинских аватаров (c→с, a→а, e→е, p→р, o→о, x→х, y→у, t→т)
  - Обработка римских цифр (I, II, III, IV, V, X, L, C, D, M)
  - Детект смешанных скриптов (латиница + кириллица)
  - For foreign docs — упрощённая нормализация
- Извлечение кодов классификации из текста (МКС/ОКС, ОКСТУ, УДК, год) — регулярные выражения
- Определение эры документа по году
- Состав полей для `classification_status` JSONB
- Связь с таблицами: `terminology_registry`, `classifier_registry`, `documents`

**Родительские изменения:**
- `specificity.md` — при необходимости
- `glossary.md` — новые термины если нужны

---

### 2. Блок: Скрипт импорта МКС/ОКС — CSV-таблица

Создать `docs/specifications/mks_oks_classifier.csv`

**Что включить:**
- Источник: ОК 001-2021 (ИСО МКС) — law.tks.ru
- Структура CSV: `code`, `parent_code`, `full_name`, `level`
- Трёхуровневая иерархия:
  - Раздел (XX): `01`, `47`
  - Группа (XX.XXX): `01.040`, `47.020`
  - Подгруппа (XX.XXX.XX): `01.040.01`, `47.020.30`
- Национальные расширения (XX.XXX.XX-XX)
- Валидатор: `^\d{2}(?:\.\d{3}(?:\.\d{2})?)?(?:-\d{2})?$`
- Предупреждение о недопустимости усечённых кодов (`31.24` вместо `31.240`)

**Родительские изменения:**
- `registry_service_api.md` — группа classifiers: добавить описание формата импорта, валидацию
- `glossary.md` — добавить/уточнить термины по структуре кодов МКС

---

### 3. Блок: Seed-данные корневых узлов классификаторов — CSV-таблица

Создать `docs/specifications/classifier_roots.csv`

**Структура:** `classifier_system`, `code`, `parent_code`, `full_name`, `status`

**Записи:**
| system | code | parent_code | full_name | status |
|--------|------|-------------|-----------|--------|
| MKS | MKS_ROOT | NULL | Межгосударственный классификатор (МКС) | active |
| OKSTU | OKSTU_ROOT | NULL | Общесоюзный классификатор (ОКСТУ) | active |
| UDC | UDC_ROOT | NULL | Универсальная десятичная классификация | active |
| EXTERNAL | EXT_ROOT | NULL | Внешние системы (DNV, ASTM, ОСТ, ТУ) | active |

**Родительские изменения:**
- `registry_service_api.md` — добавить примечание о корневых узлах
- Указать, что иерархия загружается из CSV (п.2), а корни — из этого seed

---

### 4. Блок: CAS (Content-Addressable Storage) — детальное описание

Добавить раздел в `docs/specifications/` или расширить `db_diagrams.md`

**Что включить:**
- Понятие CAS: почему hash-based пути, а не имена файлов
- Структура пути: `documents/{doc_id}/v{version}/{file_hash_sha256}` — чистый хэш
- Опционально: прикрепление оригинального имени для отладки: `{doc_id}/v{version}/{hash_prefix}_{safe_filename}`
- `hash_prefix` = первые 12 символов SHA-256
- `safe_filename` = исходное имя, очищенное от небезопасных символов (пробелы → _, только буквы/цифры/точка/дефис/подчёркивание/скобки)
- Как вычисляется content_hash_sha256 (по бинарному содержимому файла)
- Как гарантируется уникальность: UNIQUE constraint на content_hash_sha256

**Важно:** в текущей архитектуре файл грузится сразу при загрузке, хэш вычисляется по содержимому. Оригинальное имя файла известно — его можно использовать для safe_filename.

**Родительские изменения:**
- `glossary.md` — уточнить термин "CAS-путь"
- `db_diagrams.md` — примечание 4 (document_versions)
- `registry_service_api.md` — модель 5.5 (format_registry)
- `pipeline1-formation.md` — процедура загрузки

---

### 5. Блок: UNIQUE constraint на file_hash_sha256

Добавить UNIQUE-ограничение на `file_hash_sha256` в `registry.document_versions`

**Родительские изменения:**
- `db_diagrams.md` — таблица registry.document_versions: `text file_hash_sha256 UNIQUE "CAS-дедупликация"`
- `registry_service_api.md` — модель 5.5 (registry_document): уточнить ограничение
- `db_diagrams.md` — раздел "Ключевые условия и ограничения": добавить строку

---

### 6. Блок: Статусы classification_status — спецификация JSONB

В модели 5.4 `registry_document` (registry_service_api.md) уточнить структуру `classification_status`

**Формат:**
```json
{
  "mks_status": "CONFIRMED | PENDING_REVIEW | NOT_FOUND | NOT_USED | UNASSIGNED",
  "okstu_status": "CONFIRMED | PENDING_REVIEW | NOT_FOUND | NOT_USED | UNASSIGNED",
  "udk_code": "string | null",
  "extracted_at": "timestamp | null",
  "extracted_by": "string",
  "confidence": "float (0..1)"
}
```

**Набор статусов:**
| Значение | Отображение | Значение |
|----------|-------------|----------|
| CONFIRMED | ✅ | Код найден и верифицирован |
| PENDING_REVIEW | \<PENDING\> | Извлечён автоматически, требует подтверждения |
| NOT_FOUND | \<NOT_FOUND\> | Парсер не обнаружил код на первых страницах |
| NOT_USED | \<NOT_USED\> | Не применяется для данной эры/типа |
| UNASSIGNED | \<FREE\> | Классификация не назначалась |

**Родительские изменения:**
- `registry_service_api.md` — модель 5.4: поле `classification_status` с детальной спецификацией
- `registry_service_api.md` — эндпоинт 1.12 (уже есть, проверить синхронизацию)

---

### 7. Блок: Текстовое описание FK-связей

Добавить в `db_diagrams.md` после ER-диаграммы

**Формат:**
| Дочерняя таблица | Поле | Родительская таблица | Поле | Тип связи |
|-----------------|------|---------------------|------|----------|
| `registry.document_sections` | `document_id` | `registry.documents` | `id` | M:1 |
| `registry.document_versions` | `document_id` | `registry.documents` | `id` | M:1 CASCADE |
| ... | ... | ... | ... | ... |

Охватить все таблицы: documents, document_sections, document_references, document_versions, document_history, drafts, document_categories, pkb_domains.

**Родительские изменения:**
- `db_diagrams.md` — новый раздел после ER-диаграммы

---

### 8. Блок: Структура кодов МКС/ОКС — описание с regex

Добавить описание формата кодов МКС/ОКС в документацию

**Что включить:**
- Трёхуровневая иерархия: раздел (XX), группа (XX.XXX), подгруппа (XX.XXX.XX)
- Национальные расширения: XX.XXX.XX-XX
- Регулярное выражение валидации: `^\d{2}(?:\.\d{3}(?:\.\d{2})?)?(?:-\d{2})?$`
- Источник: ОК 001-2021 (ИСО МКС)
- Примеры: `47` (раздел), `47.020` (группа), `47.020.30` (подгруппа), `27.010-01` (нац. расширение)
- Запрет на усечённые коды: `31.240` — корректно, `31.24` — недопустимо

**Родительские изменения:**
- `registry_service_api.md` — группа classifiers: введение с описанием системы кодирования
- `glossary.md` — уточнить термины МКС/ОКС

---

### 9. Блок: source_filename + uploaded_by в document_versions

Добавить поля в `registry.document_versions`

- `source_filename TEXT` — оригинальное имя загруженного файла
- `uploaded_by TEXT` — идентификатор пользователя/сервиса, загрузившего версию
- (проверить) `uploaded_at` — уже есть

**Проверить черновики (`registry.drafts`):**
- `created_by` — уже есть
- `updated_by` — уже есть
- `uploaded_by` — отсутствует (если upload отличается от create — добавить)
- `source_filename` — отсутствует (если файл черновика имеет оригинальное имя)

**Родительские изменения:**
- `db_diagrams.md` — таблица registry.document_versions
- `registry_service_api.md` — модель 5.5 (format_registry) и модель 5.4 (registry_document)

---

### 10. Блок: Частичные индексы (опционально) ⚠️

Для 10 тыс. документов частичные индексы дают ограниченный выигрыш. Добавить как рекомендацию для будущего масштабирования >100k документов.

```sql
-- Пример (не включать в текущую DDL, только как примечание):
CREATE INDEX idx_docs_mks_active ON registry.documents(mks_oks_code) 
  WHERE validity_status = 'active';
CREATE INDEX idx_docs_okstu_ussr ON registry.documents(okstu_code) 
  WHERE era = 'USSR';
```

**Родительские изменения:**
- `db_diagrams.md` — добавить примечание в раздел индексов (опционально)

---

### 11. Блок: Сценарии использования — отложено 🔄

Требуется детальный разбор с заказчиком. Не включать в текущий план.

---

## Порядок выполнения

1. Создать CSV-таблицы (п.2, п.3) — независимые артефакты
2. Описать CAS (п.4) — база для понимания хранения
3. Описать нормализатор (п.1) — новый раздел, ядро дедупликации
4. Внести изменения в существующие файлы (п.5, п.6, п.7, п.8, п.9)
5. Синхронизировать с `specificity.md` и `glossary.md`
6. Проверить целостность и связанность

## Не включать (решение)
- ❌ Триггеры БД — все изменения пишут сервисы в транзакциях
- ❌ Docker-конфигурация — композ делают разработчики сервисов
- ❌ Частичные индексы в DDL — для 10k документов избыточно
