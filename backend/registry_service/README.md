Registry API
==========================

В этой директории хроняться/разрабатываются коды для Registry Service API 
(входящие запросы к системе).


[Общие постановления](../../../docs/api/common.md)

- Базовый URL: `https://{host}:8084/api/v1`
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

## Инсталляция базы данных

Перед первым запуском сервера надо сделфть пользователя БД и присвоить ему праваю. Для этого можно воспользоваться скриптом ```install/user_grants.py```. **Обратите внимание:** Скрипт должен быть запущен с правами суперпользователя (root). Результатом будет создание пользователя БД с заданными правами.

Структуру базы данных сервер сам инсталлирует при первом запуске. Этот скрипт загружает в базу данных базовые данные:
* enums
* classifiers

После первого запуска сервера надо загрузить в базу данных:
``` python install/load_data.py```


# Статусы разработки API

## 1. Классификаторы
| METHOD | EndPoint                                       | Описание                            | Статус      | Комментарии          |
|--------|------------------------------------------------|-------------------------------------|-------------|----------------------|
| GET    | /registry/classifiers/                         | Список классификаторов              | Реализовано |                      |
| GET    | /registry/classifiers/tree                     | Деревянная иерархия классификаторов | Реализовано |                      |
| GET    | /registry/classifiers/{code}                   | Получить один классификатор         | Реализовано |                      |
| POST   | /registry/classifiers/                         | Создать классификатор               | Реализовано |                      |
| PUT    | /registry/classifiers/{code}                   | Полное обновление классификатора    | Реализовано |                      |
| PATCH  | /registry/classifiers/{code}                   | Частичное обновление                | Реализовано |                      |
| DELETE | /registry/classifiers/{code}                   | Удалить классификатор               | Реализовано |                      |
| POST   | /registry/classifiers/import                   | Импорт классификаторов              | Реализовано | Заглушка             |
| GET    | /registry/classifiers/pending                  | Список карантина классификаторов    | Реализовано |                      |
| POST   | /registry/classifiers/pending/{id}/accept      | Принять код из карантина            | Реализовано |                      |
| POST   | /registry/classifiers/pending/{id}/reject      | Отклонить код из карантина          | Реализовано |                      |
| POST   | /registry/classifiers/validate                 | Валидация классификации             | Реализовано |                      |

## 2. Термины
| METHOD | EndPoint                              | Описание                                | Статус      | Комментарии          |
|--------|---------------------------------------|-----------------------------------------|-------------|----------------------|
| GET    | /registry/terminology/                 | Список терминов                          | Реализовано |                      |
| GET    | /registry/terminology/{term_id}        | Получить термин                         | Реализовано |                      |
| POST   | /registry/terminology/                 | Создать термин                          | Реализовано |                      |
| PUT    | /registry/terminology/{term_id}        | Полное обновление термина               | Реализовано |                      |
| PATCH  | /registry/terminology/{term_id}        | Частичное обновление                   | Реализовано |                      |
| DELETE | /registry/terminology/{term_id}        | Удалить термин                          | Реализовано |                      |
| GET    | /registry/terminology/normalize       | Нормализация/поиск термина              | Реализовано |                      |
| POST   | /registry/terminology/import          | Импорт терминов                         | Реализовано | Заглушка             |

## 3. Реестр документов НСИ
| METHOD | EndPoint                                    | Описание                                 | Статус      | Комментарии          |
|--------|---------------------------------------------|------------------------------------------|-------------|----------------------|
| GET    | /registry/documents/                         | Список документов                         | Реализовано |                      |
| GET    | /registry/documents/{document_id}           | Получить документ                        | Реализовано |                      |
| POST   | /registry/documents/                         | Создать документ                         | Реализовано |                      |
| PUT    | /registry/documents/{document_id}           | Полное обновление документа              | Реализовано |                      |
| PATCH  | /registry/documents/{document_id}/status    | Обновить статус документа                | Реализовано |                      |
| PATCH  | /registry/documents/{document_id}           | Частичное обновление документа           | Реализовано |                      |
| DELETE | /registry/documents/{document_id}           | Удалить документ                         | Реализовано |                      |
| GET    | /registry/documents/export                 | Экспорт документов в CSV                 | Реализовано |                      |
| POST   | /registry/documents/import                 | Импорт документов                        | Реализовано | Заглушка             |
| GET    | /registry/documents/{document_id}/history  | История изменения статусов                | Реализовано |                      |
| GET    | /registry/documents/{document_id}/succession | Цепочка преемственности документа       | Реализовано |                      |
| POST   | /registry/documents/check-uniqueness        | Проверить уникальность документа         | Реализовано |                      |
| GET    | /registry/documents/{document_id}/sections  | Секции документа (для RAG Builder)       | Реализовано |                      |
| GET    | /registry/documents/{document_id}/pages     | Список страниц документа                 | Реализовано |                      |
| GET    | /registry/documents/{document_id}/pages/{page_num} | Конкретная страница (блоки)             | Реализовано |                      |
| GET    | /registry/documents/{document_id}/pages/{page_num}/text | Текст конкретной страницы              | Реализовано |                      |
| GET    | /registry/documents/{document_id}/pages/{page_num}/preview | Превью конкретной страницы             | Реализовано |                      |
| GET    | /registry/documents/{document_id}/parameters | Извлечённые параметры документа          | Реализовано |                      |
| GET    | /registry/search                            | Полнотекстовый поиск (BM25)              | Реализовано |                      |


## 4. Черновики (Drafts)
| METHOD | EndPoint                                    | Описание                                 | Статус      | Комментарии          |
|--------|---------------------------------------------|------------------------------------------|-------------|----------------------|
| POST   | /registry/drafts                            | Создать запись черновика                 | Реализовано |                      |
| GET    | /registry/drafts                            | Список черновиков                        | Реализовано |                      |
| GET    | /registry/drafts/{draft_id}                 | Полная информация о черновике            | Реализовано |                      |
| GET    | /registry/drafts/{draft_id}/preview         | Preview-метаданные черновика             | Реализовано |                      |
| PATCH  | /registry/drafts/{draft_id}/status          | Обновить статус черновика                | Реализовано |                      |
| PATCH  | /registry/drafts/{draft_id}/metadata        | Обновить метаданные черновика            | Реализовано |                      |
| POST   | /registry/drafts/{draft_id}/snapshot        | Сохранить preview-слепок черновика       | Реализовано |                      |
| DELETE | /registry/drafts/{draft_id}                 | Удалить запись черновика                 | Реализовано |                      |

## 5. Файлы и версии (Files and Versions)
| METHOD | EndPoint                                    | Описание                                 | Статус      | Комментарии          |
|--------|---------------------------------------------|------------------------------------------|-------------|----------------------|
| GET    | /registry/files/{file_id}                   | Получить файл по ID                      | Реализовано |                      |
| GET    | /registry/documents/{document_id}/files     | Получить список файлов документа         | Реализовано |                      |
| GET    | /registry/documents/{document_id}/versions  | Получить список версий документа         | Реализовано |                      |
| GET    | /registry/versions/{version_id}             | Получить версию по ID                    | Реализовано |                      |

## 6. Категории (Categories)
| METHOD | EndPoint                                    | Описание                                 | Статус      | Комментарии          |
|--------|---------------------------------------------|------------------------------------------|-------------|----------------------|
| GET    | /registry/categories                        | Список категорий                         | Реализовано |                      |
| GET    | /registry/categories/{category_id}          | Получить категорию по ID                 | Реализовано |                      |
| PUT    | /registry/categories/{category_id}          | Обновить категорию по ID                 | Реализовано |                      |
| DELETE | /registry/categories/{category_id}          | Удалить категорию по ID                  | Реализовано |                      |

## 7. Общие
| METHOD | EndPoint            | Описание                     | Статус      | Комментарии          |
|--------|---------------------|------------------------------|-------------|----------------------|
| GET    | /registry/stats     | Статистика по реестру        | Реализовано |                      |
| GET    | /registry/enums     | Списки допустимых значений   | Реализовано |                      |

## 8. Модели данных


Таблицы находятся в общей БД, доступны напрямую всем сервисам.

Модели данных могут меняться.

## 9. Примечания

1. **DB shared:** Все таблицы registry находятся в общей БД. Другие сервисы читают их напрямую без вызова Registry Service.
2. **Импорт:** Все форматы файлов — `.xlsx` и `.csv`. Параметр `mapping` определяет соответствие колонок файла полям модели.
3. **Поиск:** Все текстовые поиски регистронезависимые (ILIKE).
4. **Валидация:** Все `POST/PUT/PATCH` валидируются через Pydantic V2 модели.
