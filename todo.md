# Fix: pdf_check тест — таймауты и dispatch

## Выполнено
1. ✅ ParserServiceClient READ_TIMEOUT → 600s
2. ✅ OCRServiceClient READ_TIMEOUT → 600s
3. ✅ Converter schema — version_id сделан опциональным (был required, но не передавался)
4. ✅ Converter service — version_id принимает None
5. ✅ Document validator — version_id принимает None, fallback-формирование хеша с '0'
6. ✅ ConvertResponse — version_id опционален
7. ✅ run_converter_full_step — удалён version_id из параметров и вызовов

## Результат теста data/pdf_tests (7 файлов)
- Upload 7/7 ✅
- Preview 7/7 ✅
- Pipeline 7/7 ✅
- Search 7/7 ✅
- Duplicate detection ✅

## Осталось
- Протестировать data/pdf_check (20 файлов, некоторые >10 MB) — может упираться в parser_timeout=300s
- MAX_CONCURRENT_TASKS=4 + очередь (не критично для тестов, но bottleneck при 20+ файлах)
