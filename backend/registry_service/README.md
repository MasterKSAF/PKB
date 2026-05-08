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
- Тест скрипты сапускаются с директории ```registry_service``` командой ```pytest```.
- Пока автоматические тесты проверяют на наличии рабочих URL.
  - следующий шаг - разработка тестов на функционал

# Статусы разработки API

## 1. Классификаторы
| METHOD | EndPoint                      | Описание                | Статус     | Коментарии    |
|--------|-------------------------------|-------------------------|------------|---------------|
| GET    | /registry/classifiers         | Список (плоский)        | GENERATED  |  |
| GET    | /registry/classifiers/tree    | Дерево (иерархическое)  | GENERATED  |  |
| GET    | /registry/classifiers/{code}  | Один узел               | GENERATED  |  |
| POST   | /registry/classifiers         | Создать                 | GENERATED  |  |
| PUT    | /registry/classifiers/{code}  | Обновить полностю       | GENERATED  |  |
| PATCH  |  /registry/classifiers/{code} | Обновить отдельные поля | GENERATED  |  |
| DELETE | /registry/classifiers/{code}  | Удалить | GENERATED  |  |
| POST  | /registry/classifiers/import  | Импорт | GENERATED |  |

## 2. Термины
| METHOD | EndPoint              | Описание                | Статус | Коментарии                                                |
|--------|-----------------------|-------------------------|--------|-----------------------------------------------------------|
| GET    | /registry/terminology | Список      | GENERATED |  |
| GET    | /registry/terminology/{term_id} | Один термин  | GENERATED |  |
| POST   | /registry/terminology | Создать      | GENERATED |  |
| PUT    | /registry/terminology/{term_id} | Обновить | GENERATED |  |
| DELETE | /registry/terminology/{term_id} | Удалить | GENERATED |  |
| GET  | /registry/terminology/normalize | Поиск нормализованной формы | GENERATED |  |
| POST  | /registry/terminology/import  | Импорт | GENERATED |  |

## 3. Реестр документов НСИ
| METHOD | EndPoint            | Описание                | Статус | Коментарии                                                |
|--------|---------------------|-------------------------|--------|-----------------------------------------------------------|
| GET    | /registry/documents | Список      | GENERATED |  |
| GET    | /registry/documents/{doc_id} | Один документ      | GENERATED |  |
| POST   | /registry/documents | Создать      | GENERATED |  |
| PUT    | /registry/documents/{doc_id | Обновить      | GENERATED |  |
| PATCH  | /registry/documents/{doc_id}/status | Обновить статус      | GENERATED |  |
| DELETE | /registry/documents/{doc_id} | Удалить      | GENERATED |  |
| GET   | /registry/documents/export | Экспорт      | GENERATED |  |
| POST   | /registry/documents/import | Массовый импорт      | GENERATED |  |

## 4. Общие
| METHOD | EndPoint            | Описание                | Статус | Коментарии                                                |
|--------|---------------------|-------------------------|--------|-----------------------------------------------------------|
| GET    | /registry/stats | Статистика      | GENERATED |  |
| GET    | /registry/enums | Допустимые значения      | GENERATED |  |

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
