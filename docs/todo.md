# Todo: Адаптация опыта Purgatory (13.06)

## Статус: ✅ Выполнено

---

## Что сделано

### 1. Нормализатор — новый раздел документации
**Файл:** `specifications/normalizer_specification.md`
- Формула бизнес-ключа
- Алгоритм нормализации (аватары, римские цифры, смешанные скрипты)
- Извлечение кодов классификации (МКС, ОКСТУ, УДК, год)
- Определение эры по году
- Спецификация classification_status JSONB (5 статусов)
- Связь с таблицами, примеры работы, обработка спорных случаев

### 2. CSV-таблица справочника МКС/ОКС
**Файл:** `specifications/mks_oks_classifier.csv`
- ~490 записей: разделы (01-97), группы, подгруппы, нац. расширения
- Структура: classifier_system, code, parent_code, full_name, level, status
- Источник: ОК 001-2021 (ИСО МКС)

### 3. CSV-таблица корневых узлов классификаторов
**Файл:** `specifications/classifier_roots.csv`
- 4 записи: MKS_ROOT, OKSTU_ROOT, UDC_ROOT, EXT_ROOT

### 4. CAS-спецификация
**Файл:** `specifications/cas_storage_specification.md`
- Понятие CAS, структура пути, hash_prefix, safe_filename
- Вычисление хэша, UNIQUE constraint, lifecycle diagram
- Обработка ошибок, связь с компонентами, сравнение с именными путями

### 5. UNIQUE constraint на file_hash_sha256
- `db_diagrams.md` — ER-диаграмма и ключевые условия
- `registry_service_api.md` — примечание к модели 5.5

### 6. Статусы classification_status — спецификация JSONB
- `registry_service_api.md` — модель 5.4: детальная спецификация
- 5 статусов: CONFIRMED, PENDING_REVIEW, NOT_FOUND, NOT_USED, UNASSIGNED
- Пример JSONB, таблица полей и значений

### 7. Текстовое описание FK-связей
- `db_diagrams.md` — новая таблица после ER-диаграммы (23 связи)
- Охвачены все таблицы: documents, sections, versions, references, history, chunks, categories, tasks, sessions, messages

### 8. Структура кодов МКС/ОКС
- `registry_service_api.md` — введение к группе classifiers с трёхуровневой иерархией и regex-валидатором
- `glossary.md` — уточнены термины МКС, ОКС, ОКСТУ, УДК, CAS, бизнес-ключ

### 9. source_filename + uploaded_by в document_versions и drafts
- `db_diagrams.md` — ER-диаграмма и примечания для обоих таблиц

### 10. Сценарии использования
**Файл:** `specifications/purgatory_scenario.md`
- Сценарии А-Е: загрузка, ввод без файла, разные форматы, дубликат, foreign документ, пустой документ
- Таблица ключевых принципов

### 11. README.md
- Обновлена структура документации — добавлены ссылки на все новые файлы

## Не включалось (согласно решению)
- ❌ Триггеры БД — все изменения пишут сервисы в транзакциях
- ❌ Docker-конфигурация — композ делают разработчики сервисов
- ❌ Частичные индексы в DDL — для 10k документов избыточно

## Что требует внимания при ревью
- `registry_service_api.md` — модель 5.4 (registry_document) была расширена спецификацией classification_status. Проверить, что её структура корректна для реальных данных.
- `db_diagrams.md` — таблица FK-связей может потребовать уточнения типов связей (каскадные удаления, nullable).
