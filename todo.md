# Fix: сканированные PDF — ошибка «Проверку черновика завершить не удалось»

## Что сделано
- [x] Converter-validator: перехват MetadataExtractionFailedError → 200 с пустыми полями вместо 422
- [x] Orchestrator: validated=False при пустых метаданных → срабатывает OCR fallback
- [x] API: error_code + error_message добавлены в TaskStatusResponse (GET /tasks/{id})
- [x] Frontend: отображение конкретной причины ошибки в уведомлении
- [x] Тесты: 22/22 converter-validator, 555/555 orchestrator (3 pre-existing)
- [x] specificity.md: запись G12
