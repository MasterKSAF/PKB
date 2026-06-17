# Модуль проверки качества текстового слоя PDF

Этот модуль выделен из утилиты аудита PDF в форму, удобную для микросервиса логического парсера документов.

Он не делает OCR и не исправляет PDF. Его задача - быстро оценить уже существующий текстовый слой: можно ли доверять извлеченному тексту, нужно ли включать OCR/альтернативное извлечение, или входной PDF вообще не удалось прочитать.

## Файлы

- `pdf_text_quality_module.py` - готовый Python-модуль.
- `pdf_text_quality_module_README.md` - это описание.

## Настройка окружения

Минимально нужен Python 3.10+.

Для проверки уже извлеченного текста внешние зависимости не нужны:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Для проверки PDF-файла нужен PyMuPDF:

```bash
python -m pip install PyMuPDF
```

Если используется Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install PyMuPDF
```

Если модуль кладется в общий пакет проекта, рекомендуемая структура такая:

```text
backend/
  shared/
    pdf_text_quality/
      __init__.py
      pdf_text_quality_module.py
      README.md
```

## Быстрое использование

Рекомендуемый импорт внутри микросервисов проекта:

```python
from shared.pdf_text_quality import analyze_pdf_file, analyze_text, assess_pdf_file, assess_text
```

Проверить PDF и получить только код:

```python
from shared.pdf_text_quality import assess_pdf_file

code = assess_pdf_file("docs/example.pdf", pages_limit=5)
```

Проверить уже извлеченный текст и получить только код:

```python
from shared.pdf_text_quality import assess_text

text = "ГОСТ 20868-81. Оборудование..."
code = assess_text(text)
```

Получить подробный результат для логов:

```python
from shared.pdf_text_quality import analyze_pdf_file, result_to_log_message

result = analyze_pdf_file("docs/example.pdf", pages_limit=5)

logger.info(result_to_log_message(result))
logger.info(result.to_dict())
```

Если сервис сам извлекает текст из PDF, лучше использовать `analyze_text()`:

```python
from shared.pdf_text_quality import analyze_text

text = my_pdf_reader.extract_text(file_bytes)
result = analyze_text(text, source_name="example.pdf")

if result.needs_ocr:
    run_ocr_pipeline()
```

## Импорт в микросервисах

Пакет `shared` лежит внутри папки `backend`, поэтому при запуске микросервиса папка `backend` должна быть доступна в `PYTHONPATH`.

Если импорт ниже не находится:

```python
from shared.pdf_text_quality import analyze_pdf_file, assess_text
```

проверьте рабочую папку запуска сервиса или добавьте `backend` в `PYTHONPATH`.

Автономный импорт напрямую из файла тоже возможен, если модуль лежит рядом с кодом:

```python
from pdf_text_quality_module import analyze_pdf_file, assess_text
```

## Основные функции

### `assess_pdf_file(pdf_path, pages_limit=5) -> int`

Открывает PDF через PyMuPDF, берет текстовый слой с первых `pages_limit` страниц и возвращает только числовой код пригодности.

Подходит для простой развилки в пайплайне.

### `assess_text(text) -> int`

Проверяет уже извлеченный текст и возвращает только числовой код пригодности.

Эта функция удобна, если микросервис логического парсера использует свой способ чтения PDF.

### `analyze_pdf_file(pdf_path, pages_limit=5) -> TextQualityResult`

Возвращает подробный объект результата: код, балл, маркеры проблем, человеко-понятное описание, метрики, пример текста.

### `analyze_text(text, ...) -> TextQualityResult`

То же самое, но без чтения PDF-файла. На вход подается обычная строка.

### `decode_quality_code(code) -> str`

Возвращает человеко-понятную расшифровку кода. Удобно для логгера.

```python
from shared.pdf_text_quality import decode_quality_code

print(decode_quality_code(2))
```

### `quality_code_info(code) -> dict`

Возвращает структурированную расшифровку кода для API-ответа или JSON-логов.

## Коды пригодности

| Код | Имя | Значение для пайплайна |
| --- | --- | --- |
| `0` | `GOOD` | Текстовый слой хороший. Можно передавать текст в логический парсер. |
| `1` | `SUSPECT` | Текстовый слой подозрительный. Парсинг возможен, но результат нужно логировать как рискованный или проверить альтернативным способом. |
| `2` | `BAD` | Текстовый слой плохой или отсутствует. Нужен OCR или альтернативное извлечение. |
| `3` | `PDF_READ_ERROR` | PDF не удалось открыть или прочитать. Это техническая ошибка входного файла. |

Практическая развилка:

```python
from shared.pdf_text_quality import TextLayerQualityCode, analyze_text

result = analyze_text(text)

if result.code == TextLayerQualityCode.GOOD:
    parse_logical_structure(text)
elif result.code == TextLayerQualityCode.SUSPECT:
    logger.warning(result.problem_ru)
    parse_logical_structure(text)
elif result.code == TextLayerQualityCode.BAD:
    run_ocr_pipeline()
else:
    mark_document_as_failed(result.error)
```

## Что проверяет модуль

Модуль считает:

- общий объем извлеченного текста;
- долю кириллицы, латиницы, цифр и пробелов;
- количество знаков вопроса `?`, когда они выглядят как замена символов;
- символы замены `�`;
- долю непечатаемых или нестандартных символов;
- явные маркеры битой кодировки старых русскоязычных PDF;
- псевдолатиницу вместо русского текста, например фрагменты вида `KLASSIFIKACII`, `pRAWILA`, `OBSLUVIWANIQ`.

Внутри результата также есть `score` от 0 до 100:

- `80..100` -> `GOOD`;
- `50..79` -> `SUSPECT`;
- `0..49` -> `BAD`.

## Поля подробного результата

`TextQualityResult` содержит:

- `code` - числовой код;
- `code_name` - имя кода;
- `code_ru` - короткое русское название;
- `score` - внутренний балл качества от 0 до 100;
- `is_usable` - можно ли уверенно использовать текст;
- `needs_ocr` - нужен ли OCR;
- `problem_ru` - человеко-понятное описание проблемы;
- `language_detected` - грубая оценка письменности: `CYRILLIC`, `LATIN`, `MIXED`, `UNKNOWN`;
- `markers` - технические маркеры проблем;
- `markers_ru` - русские расшифровки маркеров;
- `metrics` - численные метрики;
- `sample_text` - первые 500 символов нормализованного текста;
- `source_name`, `source_path`, `file_size_mb`, `pages_total`, `pages_scanned` - сведения об источнике;
- `error` - текст ошибки, если PDF не удалось прочитать.

## CLI для быстрой проверки

Модуль можно запустить как маленькую утилиту:

```bash
python pdf_text_quality_module.py docs/example.pdf
python pdf_text_quality_module.py docs/example.pdf --json
python pdf_text_quality_module.py "ГОСТ 20868-81. Текст..." --text --json
```

Для микросервиса CLI не нужен, но он удобен для ручной проверки при отладке.
