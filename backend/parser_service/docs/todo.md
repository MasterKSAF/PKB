todo на 14.06.2026:
- настроить подключение к MinIO



12.06.2026 внесены изменения:
- Сервис настроен и подключен(локально) к системе мониторинга



10.06.2026 реализована 2v parser_service 
Со следующими изменениями: 
  * Разделение API на v1 и v2  
  – v1 сохранён для обратной совместимости, v2 добавлен с префиксом `/api/v2`.  
  – В v2 эндпоинт `/process` объединяет `full` и `preview` через параметр `mode`; отдельный `/preview` удалён.  
  – Из запросов v2 убрано поле `version_id`, упрощены ответы.  
  * Рефакторинг хранилища задач  
    – `TaskStateStorage` теперь сам управляет блокировками (`asyncio.Lock` на задачу), TTL и уведомлениями.  
    – Удалён `TaskResultCache` (заглушка).  
    – `TaskEventNotifier` дополнен хранением `_versions` для корректного long polling (проверка версии в цикле).  
  * Изменение обработки изображений  
    – Парсеры (`PdfParser`) больше не загружают изображения в MinIO, а сохраняют их во временные файлы и возвращают пути (`ParseResult.images` → список `(page_num, file_path, ext)`).  
    – Добавлен шаг `UploadImagesStep`: загружает файлы в MinIO, заменяет пути в JSON на `image_key`, удаляет временные файлы.  
    – `Normalizer` упрощён (только обёртка JSON), логика загрузки вынесена.
    – Файлы теперь сохраняютс по пути task_id/{task_id}_{num_image}_{hash}.png в бакете MinIO parser-image.
    – Значения высоты и ширины в итоговом json переведены в значения пикселей. 
  * Новая утилита `file_loader.py`  
    – Единая функция `fetch_and_validate` для скачивания и валидации файла (используется в preview и v2 preview).  
  * Graceful shutdown  
    – В `main.py` создан `shutdown_event`, передаётся в пайплайн через `ProcessingContext`.  
    – Пайплайн проверяет событие перед каждым шагом и выбрасывает `CancelledError`.  
  * Построение результата через `ResultBuilder`  
    – Вместо ручного формирования JSON в `StoreResultStep` используется `ResultBuilder.build()`, унифицирующий формат для v1 и v2.  
  * Пайплайн: фабричный метод `Pipeline.create(mode, track_progress)`  
    – Режимы `full` и `preview` собирают разные наборы шагов (в preview отсутствует `UploadImagesStep` и `SaveJsonToFileStep`).  
    – Добавлен шаг `PagesTotalStep` (определение числа страниц через pypdf до парсинга).  
  * Таймауты  
    – Добавлен `parser_timeout` (отдельно от `pipeline_timeout`).  
    – `PdfParser.parse()` обёрнут в `asyncio.wait_for` с `parser_timeout`.  
    – В `_run_full_pipeline` добавлен общий таймаут `pipeline_timeout`.  
  * Поддержка только PDF  
    – Из `SUPPORTED_MIME_TYPES` удалены `application/msword` и `docx`; фабрика парсеров теперь только `application/pdf`.  
  * Логирование  
    – Добавлен `logging.py` с JSON-форматом через `pythonjsonlogger`.  
    – Логгер инициализируется в `main.py` до всех остальных импортов.  
  * MinIO клиент  
    – Добавлен `_ensure_bucket` (создание бакетов при старте).  
    – Настроены таймауты через `botocore.config.Config`.  
    – `upload_image` принимает опциональный `custom_key`.  
  * Обработка ошибок  
    – `exception_handlers.py` перемещён в `core`, улучшена обработка `ValueError` из Pydantic.  
    – В `result.py` (v1) и v2 `get_task_result` возвращает `JSONResponse` вместо `raise HTTPException` для единообразия.  
  * Удалены неиспользуемые компоненты  
    – `task_result_cache.py` удалён.  
    – `image_uploader.py` и `MinIOImageUploader` удалены (заменены `UploadImagesStep`).
  * Замена подписи схемы на raw_ocr_v4.
  


02.06.2026 реализована 1v parser_service
