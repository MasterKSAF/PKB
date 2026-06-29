# Тест загрузки + детальный вывод шагов + анализ багов

- [x] 1. Изучить проект, Docker, существующие тесты
- [x] 2. Создать `data/tests/test_universal_pdf_loader.py`
- [x] 3. Добавить детальный вывод шагов в тест:
  - группировка по step_name со статусами
  - подсветка pending/failed/duplicate
  - документ_id в поиске для понимания какой документ найден
- [x] 4. Запустить тест с НД №2 (249 стр. PDF)
- [ ] 5. Полный E2E прогон — **требует фикса багов в orchestrator**

## Найденные баги (описаны в specificity.md)

### B1. Циклический OCR fallback — preview_ocr дублируется
- `_run_ocr_fallback` проверяет только `pending`, не проверяет `completed` OCR-шаги
- Цикл: Parser → Converter fail → OCR → Converter fail → OCR → ...
- Фикс: guard должен проверять completed OCR Service

### B2. full_ocr (Parser) не завершается на больших PDF
- full_ocr висит `running` >300с на 249 страницах
- Все downstream шаги (converter, registry, rag) заблокированы

### B3. RAG-индексация не стартует
- rag_index стартуется только через цепочку full_ocr → converter → registry → rag
- Если full_ocr висит — rag_index никогда не стартует
- При этом RAG Builder находит данные (поиск работает) — pipeline не синхронизирован
