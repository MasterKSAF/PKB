Registry API
==========================

В этой директории хроняться/разрабатываются коды для Registry Service API 
(входящие запросы к системе).


[Общие постановления](../../../docs/api/common.md)

- Базовый URL: `https://{host}/api/v1`
- Базовые документы находятся в ```docs/api```

- Запуск сервера в среде разработчика производится из директории ```registry_service``` командой:
```commandline
uvicorn main:app --reload --port 8084
```
Потом смотреть по адресу: ```http://127.0.0.1:8084/api/v1``` и дальше добавить по описанию.

- Тест скрипты сапускаются с директории ```registry_service``` командой ```pytest```.
- Пока автоматические тесты проверяют на наличии рабочих URL.
  - следующий шаг - разработка тестов на функционал

# Окружение и конфигурация

## Переменные окружения

Сервис требует следующие переменные окружения, определённые в файле `.env` в корне директории `registry_service`:

```env
DB_USERNAME=<database_user>
DB_PASSWORD=<database_password>
DB_HOST=<database_host>
DB_PORT=<database_port>
DB_DATABASE=<database_name>
```

**Описание переменных:**
- `DB_USERNAME` — пользователь PostgreSQL
- `DB_PASSWORD` — пароль пользователя
- `DB_HOST` — хост БД (например: 127.0.0.1)
- `DB_PORT` — порт PostgreSQL (по умолчанию: 5432)
- `DB_DATABASE` — имя базы данных

Файл `.env` **не должен** включаться в систему контроля версий (уже добавлен в `.gitignore`).

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
| PUT    | /registry/documents/{doc_id} | Обновить      | GENERATED |  |
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

Модели данных могут меняться.

## 6. Примечания

1. **DB shared:** Все таблицы registry находятся в общей БД. Другие сервисы читают их напрямую без вызова Registry Service.
2. **Импорт:** Все форматы файлов — `.xlsx` и `.csv`. Параметр `mapping` определяет соответствие колонок файла полям модели.
3. **Поиск:** Все текстовые поиски регистронезависимые (ILIKE).
4. **Валидация:** Все `POST/PUT/PATCH` валидируются через Pydantic V2 модели.
