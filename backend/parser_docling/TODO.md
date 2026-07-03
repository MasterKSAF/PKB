# parser_docling — план сессии

## Выполнено
- [x] Установка зависимостей docling
- [x] compare_json.py — расширенное сравнение с ODO
- [x] evaluate_quality.py — Precision/Recall/F1 через сырой PDF
- [x] Починен pipeline: батчи по 5 стр. (std::bad_alloc)
- [x] Enrich: заполнение пустых блоков через PyMuPDF
- [x] Enrich: конвертация BOTTOMLEFT → Screen координат
- [x] Добавление колонтитулов (строки, пропущенные Docling)
- [x] DocumentConverter протестирован (≤5 стр. работает)
- [x] Итог: Precision=0.993, Recall=0.996, F1=0.995, Confidence=0.75
