# План — фикс сервисов с неверными данными

## Проблема
Checker шлёт сервисам некорректные/неполные данные.

## План
### [ ] 1. RAG Builder — вернуть document_id в секции
- Сервис требует document_id в каждой секции, checker его убрал
- [ ] 1.1 `services/rag_builder.py`
- [ ] 1.2 `pipelines/document_processing.py`
- [ ] 1.3 `pipelines/full_document_lifecycle.py`
- [ ] 1.4 `pipelines/multi_document_cross_search.py`

### [ ] 2. Converter-Validator — preview + validate/document
- [ ] 2.1 `services/converter_validator.py` — слать минимальный валидный ParserResult

### [ ] 3. Тесты
- [ ] 3.1 Запустить unit-тесты
- [ ] 3.2 Запустить recheck.bat

### [ ] 4. Документация
- [ ] 4.1 specificity.md — записать изменения
- [ ] 4.2 todo.md — отметить выполненное
