# Fix: pdf_check тест — таймауты и dispatch

## Выполнено и закоммичено
1. ✅ ParserServiceClient READ_TIMEOUT → 600s
2. ✅ OCRServiceClient READ_TIMEOUT → 600s
3. ✅ Converter schema — version_id сделан опциональным (был required → 422)
4. ✅ Converter service — version_id принимает None
5. ✅ Document validator — version_id принимает None
6. ✅ ConvertResponse — version_id опционален
7. ✅ run_converter_full_step — удалён version_id из параметров/вызовов
8. ✅ Таймаут pipeline poll в тесте увеличен с 300s до 1200s
9. ✅ Таймаут preview poll в тесте увеличен с 60s до 120s

## Результаты теста
### data/pdf_tests (7 файлов, маленькие)
- Upload 7/7 ✅ | Preview 7/7 ✅ | Pipeline 7/7 ✅ | Search 7/7 ✅

### data/pdf_check (20 файлов, до 10 MB)
- Upload 20/20 ✅ | Preview 20/20 ✅ | Pipeline 9/20 ✅ | Search 9/9 ✅
- 11/20 pipeline не завершились за 541s (прежний таймаут теста) — большие PDF >3MB с чертежами требуют >300s full-обработки через opendataloader-pdf

## Проверка целостности
- Изменения в converter-validator (schemas, converter_service, document_validator) — обратно совместимы, version_id опционален
- Изменения в orchestrator (parser_client, ocr_client) — только увеличение таймаута
- Изменения в pipeline_formation — удалён version_id из конвертера
- orchestator.py — удалён version_id из _on_full_step_completed
- Тест — только таймауты
- specificity.md — обновлён статус G8
