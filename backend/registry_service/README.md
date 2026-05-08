Registry API
==========================

В этой директории хроняться/разрабатываются коды для Registry Service API 
(входящие запросы к системе).


[Общие постановления](../../../docs/api/common.md)

- Базовый URL: `https://{host}/api/v1`
- Базовые документы находятся в ```docs/api```

- Запуск сервера в среде разработчика производится из директории ```registry_service``` командой (порт по усмотрению):
```commandline
uvicorn main:app --reload --port 8100
```
Потом смотреть по адресу: ```http://27.0.0.1:8100/api/v1``` и дальше добавить по описанию.

- На производстве порт будет 80 и запуск из докера.

- в среде разработки можно сделать локальный файл ```..\registry_service\env.py``` который не загружаеться на GitHub,
с записями указанными ниже

```
os.environ.setdefault("DB_DATABASE","<database>")
os.environ.setdefault("DB_PASSWORD", "<user_password>")
os.environ.setdefault("DB_USERNAME", "<username>")
os.environ.setdefault("DB_HOST", "<host>")
os.environ.setdefault("DB_PORT", "<port>")
```

# Статусы разработки API

## 1. Классификаторы
| METHOD | EndPoint                      | Описание                | Статус | Коментарии    |
|--------|-------------------------------|-------------------------|--------|---------------|
| GET    | /registry/classifiers         | Список (плоский)        | New    |  |
| GET    | /registry/classifiers/tree    | Дерево (иерархическое)  | New    |  |
| GET    | /registry/classifiers/{code}  | Один узел               | New    |  |
| POST   | /registry/classifiers         | Создать                 | New    |  |
| PUT    | /registry/classifiers/{code}  | Обновить полностю       | New    |  |
| PATCH  |  /registry/classifiers/{code} | Обновить отдельные поля | New    |  |
| DELETE | /registry/classifiers/{code}  | Удалить | New    |  |
| POST  | /registry/classifiers/import  | Импорт | New    |  |

## 2. Термины
| METHOD | EndPoint              | Описание                | Статус | Коментарии                                                |
|--------|-----------------------|-------------------------|--------|-----------------------------------------------------------|
| GET    | /registry/terminology | Список      | New    |  |
| GET    | /registry/terminology/{term_id} | Один термин  | New    |  |
| POST   | /registry/terminology | Создать      | New    |  |
| PUT    | /registry/terminology/{term_id} | Обновить      | New    |  |
| DELETE | /registry/terminology/{term_id} | Удалить      | New    |  |
| GET  | /registry/terminology/normalize | Поиск нормализованной формы      | New    |  |
| POST  | /registry/terminology/import  | Импорт | New    |  |

## 3. Реестр документов НСИ
| METHOD | EndPoint            | Описание                | Статус | Коментарии                                                |
|--------|---------------------|-------------------------|--------|-----------------------------------------------------------|
| GET    | /registry/documents | Список      | New    |  |
| GET    | /registry/documents/{doc_id} | Один документ      | New    |  |
| POST   | /registry/documents | Создать      | New    |  |
| PUT    | /registry/documents/{doc_id | Обновить      | New    |  |
| PATCH  | /registry/documents/{doc_id}/status | Обновить статус      | New    |  |
| DELETE | /registry/documents/{doc_id} | Удалить      | New    |  |
| GET   | /registry/documents/export | Экспорт      | New    |  |
| POST   | /registry/documents/import | Массовый импорт      | New    |  |

## 4. Общие
| METHOD | EndPoint            | Описание                | Статус | Коментарии                                                |
|--------|---------------------|-------------------------|--------|-----------------------------------------------------------|
| GET    | /registry/stats | Статистика      | New    |  |
| GET    | /registry/enums | Допустимые значения      | New    |  |

## 5. Модели данных

Таблицы находятся в общей БД, доступны напрямую всем сервисам.

### 5.1. ClassifierNode

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `code` | varchar(50) | PK |
| `parent_code` | varchar(50) | FK → classifier_registry.code, nullable |
| `full_name` | varchar(500) | NOT NULL |
| `doc_type` | varchar(20) | NOT NULL, DEFAULT 'OKS' |
| `jurisdiction` | varchar(10) | NOT NULL, DEFAULT 'RF' |
| `language` | varchar(5) | NOT NULL, DEFAULT 'ru' |
| `oks_code` | varchar(20) | nullable |
| `is_thematic` | boolean | NOT NULL, DEFAULT true |
| `created_at` | timestamptz | NOT NULL |
| `updated_at` | timestamptz | NOT NULL |

### 5.2. TerminologyEntry

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `term_id` | serial | PK |
| `term` | varchar(500) | NOT NULL |
| `normalized_term` | varchar(500) | NOT NULL |
| `context` | varchar(100) | NOT NULL, DEFAULT 'Общий' |
| `source` | varchar(500) | nullable |
| `created_at` | timestamptz | NOT NULL |
| UNIQUE | | (`term`, `context`) |

### 5.3. RegistryDocument

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `doc_id` | serial | PK |
| `title` | varchar(500) | NOT NULL |
| `doc_number` | varchar(100) | nullable |
| `classifier_code` | varchar(50) | FK → classifier_registry.code, nullable |
| `status` | varchar(20) | NOT NULL, DEFAULT 'draft' |
| `source` | varchar(500) | nullable |
| `notes` | text | nullable |
| `created_at` | timestamptz | NOT NULL |
| `updated_at` | timestamptz | NOT NULL |

---

## 6. Примечания

1. **DB shared:** Все таблицы registry находятся в общей БД. Другие сервисы читают их напрямую без вызова Registry Service.
2. **Импорт:** Все форматы файлов — `.xlsx` и `.csv`. Параметр `mapping` определяет соответствие колонок файла полям модели.
3. **Поиск:** Все текстовые поиски регистронезависимые (ILIKE).
4. **Валидация:** Все `POST/PUT/PATCH` валидируются через Pydantic V2 модели.
